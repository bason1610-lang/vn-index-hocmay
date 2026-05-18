"""
ml_utils.py
-----------
Tiện ích dùng chung cho project "Dự đoán giá cổ phiếu VN-Index dựa trên biến
động giá trong quá khứ" (HCMUTE - Học Máy).

Cách tiếp cận:
    Bài toán dự đoán giá cổ phiếu trực tiếp (price level) thường khiến các mô
    hình phi tuyến (KNN, Random Forest) thất bại vì chúng không thể ngoại suy
    ngoài miền giá trị đã thấy trong tập train; trong khi Linear Regression
    "ăn gian" bằng cách gần như sao chép giá hiện tại. Vì vậy nhóm chuyển bài
    toán về dạng *stationary*: **dự đoán lợi suất kỳ kế tiếp**
    (``r_{t+1} = Close_{t+1}/Close_t - 1``), rồi suy ngược ra giá:
        ``Close_pred_{t+1} = Close_t * (1 + r_pred)``.

Module gồm:
    1. Đọc dữ liệu thô (CSV từ yfinance).
    2. Sinh đặc trưng kỹ thuật STATIONARY (lợi suất, MA-ratio, RSI, volatility).
    3. Chia train/test theo trục thời gian (không xáo trộn).
    4. Huấn luyện và đánh giá 4 mô hình:
       Linear Regression, KNN, Random Forest, Voting Ensemble.
    5. Vẽ biểu đồ so sánh và biểu đồ dự đoán/thực tế (cả ở miền giá lẫn lợi suất).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ----------------------------------------------------------------------
# Đường dẫn mặc định (project root = thư mục cha của scripts/)
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "vcb_stock.csv"
IMAGE_DIR = PROJECT_ROOT / "image"
IMAGE_DIR.mkdir(exist_ok=True)


# Bộ đặc trưng STATIONARY — không phụ thuộc vào mức giá tuyệt đối,
# nhờ vậy các mô hình phi tuyến mới có thể tổng quát hóa.
FEATURE_COLUMNS: List[str] = [
    "Return_1", "Return_2", "Return_3", "Return_5", "Return_10",
    "MA5_Ratio", "MA10_Ratio", "MA20_Ratio",
    "Vol_5", "Vol_10",
    "RSI_14",
    "HL_Range", "OC_Range",
    "Vol_Change",
]
TARGET_COLUMN = "Target_Return"
PRICE_COLUMN = "Close"


# ----------------------------------------------------------------------
# 1. Đọc dữ liệu
# ----------------------------------------------------------------------
def load_raw_data(path: os.PathLike | str | None = None,
                  interval: str = "1d") -> pd.DataFrame:
    """Đọc CSV thô và lọc khung thời gian (mặc định 1 ngày)."""
    path = Path(path) if path else DATA_PATH
    df = pd.read_csv(path, parse_dates=["Date"])
    if "Interval" in df.columns:
        df = df[df["Interval"] == interval].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    return df


# ----------------------------------------------------------------------
# 2. Đặc trưng (feature engineering) - đã chuẩn hóa để ổn định
# ----------------------------------------------------------------------
def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Chỉ báo Relative Strength Index (rolling-mean smoothing)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Sinh đặc trưng stationary và biến mục tiêu (lợi suất kỳ kế tiếp)."""
    out = df.copy()
    close = out["Close"]

    for k in (1, 2, 3, 5, 10):
        out[f"Return_{k}"] = close.pct_change(k)

    for w in (5, 10, 20):
        out[f"MA{w}_Ratio"] = close / close.rolling(w).mean() - 1

    for w in (5, 10):
        out[f"Vol_{w}"] = close.pct_change().rolling(w).std()

    out["RSI_14"] = _rsi(close, 14)

    out["HL_Range"] = (out["High"] - out["Low"]) / close
    out["OC_Range"] = (out["Close"] - out["Open"]) / out["Open"]
    out["Vol_Change"] = out["Volume"].pct_change().replace([np.inf, -np.inf], np.nan)

    out[TARGET_COLUMN] = close.pct_change().shift(-1)

    return out.dropna().reset_index(drop=True)


def get_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    return df[FEATURE_COLUMNS].copy(), df[TARGET_COLUMN].copy()


def time_series_split(X: pd.DataFrame, y: pd.Series,
                      train_ratio: float = 0.8
                      ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    split = int(len(X) * train_ratio)
    return X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]


# ----------------------------------------------------------------------
# 3. Mô hình
# ----------------------------------------------------------------------
def get_models(random_state: int = 42) -> Dict[str, object]:
    """Bốn mô hình thử nghiệm (đều bọc Pipeline có scaler)."""
    lr = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression()),
    ])
    knn = Pipeline([
        ("scaler", StandardScaler()),
        ("model", KNeighborsRegressor(n_neighbors=15, weights="distance")),
    ])
    rf = Pipeline([
        ("scaler", StandardScaler(with_mean=False)),
        ("model", RandomForestRegressor(
            n_estimators=400,
            max_depth=8,
            min_samples_leaf=5,
            random_state=random_state,
            n_jobs=-1,
        )),
    ])
    ensemble = VotingRegressor(estimators=[
        ("lr",  Pipeline([("scaler", StandardScaler()),
                          ("model", LinearRegression())])),
        ("knn", Pipeline([("scaler", StandardScaler()),
                          ("model", KNeighborsRegressor(n_neighbors=15,
                                                         weights="distance"))])),
        ("rf",  RandomForestRegressor(
            n_estimators=400, max_depth=8, min_samples_leaf=5,
            random_state=random_state, n_jobs=-1)),
    ])
    return {
        "Linear Regression": lr,
        "KNN":               knn,
        "Random Forest":     rf,
        "Ensemble":          ensemble,
    }


def train_models(X_train: pd.DataFrame, y_train: pd.Series,
                 random_state: int = 42) -> Dict[str, object]:
    fitted: Dict[str, object] = {}
    for name, model in get_models(random_state).items():
        fitted[name] = model.fit(X_train, y_train)
    return fitted


# ----------------------------------------------------------------------
# 4. Đánh giá
# ----------------------------------------------------------------------
def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = np.abs(y_true) > 1e-9
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))
    direction_acc = float(((np.sign(y_true) == np.sign(y_pred)).mean()) * 100.0)
    return {"MAE": mae, "RMSE": rmse, "R2": r2, "DirAcc(%)": direction_acc}


def evaluate_all(fitted: Dict[str, object],
                 X_test: pd.DataFrame, y_test: pd.Series
                 ) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    """Đánh giá trên miền lợi suất (return)."""
    rows = []
    preds: Dict[str, np.ndarray] = {}
    for name, model in fitted.items():
        yhat = np.asarray(model.predict(X_test))
        preds[name] = yhat
        m = _metrics(y_test, yhat)
        m["Model"] = name
        rows.append(m)
    metrics = (pd.DataFrame(rows)
               .set_index("Model")[["MAE", "RMSE", "R2", "DirAcc(%)"]]
               .round(6))
    return metrics, preds


def to_price_predictions(close_today: pd.Series,
                         preds_return: Dict[str, np.ndarray],
                         y_true_return: pd.Series
                         ) -> Tuple[pd.Series, Dict[str, np.ndarray], pd.DataFrame]:
    """Chuyển dự đoán lợi suất thành giá để vẽ biểu đồ và đánh giá MAE/RMSE
    trên đơn vị VND (dễ trực quan hơn cho người đọc)."""
    close_today = close_today.reset_index(drop=True)
    y_true_price = close_today * (1 + y_true_return.reset_index(drop=True))
    preds_price: Dict[str, np.ndarray] = {
        name: (close_today.values * (1 + p))
        for name, p in preds_return.items()
    }
    rows = []
    for name, yp in preds_price.items():
        yt = y_true_price.values
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))
        mae  = float(mean_absolute_error(yt, yp))
        mape = _safe_mape(yt, yp)
        rows.append({"Model": name,
                     "MAE (VND)": mae,
                     "RMSE (VND)": rmse,
                     "MAPE(%)": mape})
    price_metrics = (pd.DataFrame(rows).set_index("Model").round(2))
    return y_true_price, preds_price, price_metrics


# ----------------------------------------------------------------------
# 5. Trực quan
# ----------------------------------------------------------------------
def _save(fig: plt.Figure, save_path: os.PathLike | str | None) -> plt.Figure:
    if save_path is not None:
        fig.savefig(save_path, dpi=130, bbox_inches="tight")
    return fig


def plot_price_history(df: pd.DataFrame,
                       save_path: os.PathLike | str | None = None) -> plt.Figure:
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    axes[0].plot(df["Date"], df["Close"], color="#1f77b4", linewidth=1.1)
    axes[0].set_title("VCB.VN — Giá đóng cửa theo thời gian (khung 1 ngày)")
    axes[0].set_ylabel("Giá (VND)"); axes[0].grid(alpha=.3)

    axes[1].bar(df["Date"], df["Volume"], color="#7f7f7f", width=2.0)
    axes[1].set_title("Khối lượng giao dịch")
    axes[1].set_ylabel("Volume"); axes[1].set_xlabel("Ngày")
    axes[1].grid(alpha=.3)

    fig.tight_layout()
    return _save(fig, save_path)


def plot_returns_distribution(df_feat: pd.DataFrame,
                              save_path: os.PathLike | str | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    sns.histplot(df_feat["Return_1"], bins=80, kde=True, ax=ax,
                 color="#2ca02c", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", alpha=.6)
    ax.set_title("Phân phối lợi suất ngày của VCB")
    ax.set_xlabel("Return (theo ngày)"); ax.set_ylabel("Số phiên")
    fig.tight_layout()
    return _save(fig, save_path)


def plot_correlation_heatmap(df: pd.DataFrame,
                             save_path: os.PathLike | str | None = None) -> plt.Figure:
    cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(11, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
                cbar_kws={"shrink": .8}, annot_kws={"size": 8})
    ax.set_title("Ma trận tương quan giữa các đặc trưng và biến mục tiêu (lợi suất)")
    fig.tight_layout()
    return _save(fig, save_path)


def plot_predictions_vs_actual(dates: pd.Series,
                               y_true: np.ndarray,
                               preds: Dict[str, np.ndarray],
                               title: str,
                               ylabel: str,
                               save_path: os.PathLike | str | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.plot(dates, y_true, label="Thực tế", color="black", linewidth=1.6)
    palette = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd"]
    for (name, yhat), c in zip(preds.items(), palette):
        ax.plot(dates, yhat, label=name, color=c, linewidth=1.0, alpha=.85)
    ax.set_title(title)
    ax.set_xlabel("Ngày"); ax.set_ylabel(ylabel)
    ax.legend(loc="best"); ax.grid(alpha=.3)
    fig.tight_layout()
    return _save(fig, save_path)


def plot_model_comparison(metrics: pd.DataFrame,
                          save_path: os.PathLike | str | None = None) -> plt.Figure:
    """Biểu đồ cột 4 metric (MAE, RMSE, R2, DirAcc%)."""
    cols = [c for c in ["MAE", "RMSE", "R2", "DirAcc(%)"] if c in metrics.columns]
    n = len(cols)
    fig, axes = plt.subplots(1, n, figsize=(3.4 * n, 4.4))
    if n == 1:
        axes = [axes]
    palette = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd"]
    direction = {"MAE": "thấp hơn = tốt hơn",
                 "RMSE": "thấp hơn = tốt hơn",
                 "R2": "cao hơn = tốt hơn",
                 "DirAcc(%)": "cao hơn = tốt hơn"}
    for ax, c in zip(axes, cols):
        ax.bar(metrics.index, metrics[c], color=palette[: len(metrics)])
        ax.set_title(f"{c}\n({direction[c]})", fontsize=10)
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", alpha=.3)
        for i, v in enumerate(metrics[c]):
            ax.text(i, v, f"{v:.4g}", ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=8)
    fig.suptitle("So sánh hiệu năng các mô hình", y=1.02, fontsize=13)
    fig.tight_layout()
    return _save(fig, save_path)


# ----------------------------------------------------------------------
# 6. Pipeline đầy đủ (tiện gọi từ Notebook)
# ----------------------------------------------------------------------
def run_full_pipeline(interval: str = "1d",
                      train_ratio: float = 0.8,
                      save_images: bool = True
                      ) -> Dict[str, object]:
    """Chạy toàn bộ pipeline và trả về dict kết quả."""
    raw = load_raw_data(interval=interval)
    feat = build_features(raw)
    X, y = get_xy(feat)
    X_tr, X_te, y_tr, y_te = time_series_split(X, y, train_ratio)
    fitted = train_models(X_tr, y_tr)
    metrics_ret, preds_ret = evaluate_all(fitted, X_te, y_te)

    close_test = feat[PRICE_COLUMN].iloc[len(X_tr):len(X_tr) + len(X_te)].reset_index(drop=True)
    y_true_price, preds_price, metrics_price = to_price_predictions(
        close_test, preds_ret, y_te
    )
    dates_test = feat["Date"].iloc[len(X_tr):len(X_tr) + len(X_te)].reset_index(drop=True)

    if save_images:
        plot_price_history(raw, IMAGE_DIR / "price_history_daily.png")
        plot_returns_distribution(feat, IMAGE_DIR / "returns_distribution.png")
        plot_correlation_heatmap(feat, IMAGE_DIR / "correlation_heatmap.png")
        plot_model_comparison(metrics_ret, IMAGE_DIR / "model_comparison.png")
        plot_predictions_vs_actual(
            dates_test, y_true_price.values, preds_price,
            title="Dự đoán giá đóng cửa vs. Thực tế trên tập kiểm tra (VCB)",
            ylabel="Giá đóng cửa (VND)",
            save_path=IMAGE_DIR / "predictions_vs_actual.png",
        )
        plot_predictions_vs_actual(
            dates_test, y_te.values, preds_ret,
            title="Dự đoán lợi suất vs. Thực tế trên tập kiểm tra (VCB)",
            ylabel="Lợi suất hàng ngày",
            save_path=IMAGE_DIR / "returns_vs_actual.png",
        )

    return {
        "raw": raw, "features": feat,
        "X_train": X_tr, "X_test": X_te,
        "y_train": y_tr, "y_test": y_te,
        "fitted": fitted,
        "metrics_return": metrics_ret,
        "metrics_price": metrics_price,
        "preds_return": preds_ret,
        "preds_price": preds_price,
        "dates_test": dates_test,
        "close_test": close_test,
        "y_true_price": y_true_price,
    }
