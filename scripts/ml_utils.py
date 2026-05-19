"""
ml_utils.py
-----------
Tiện ích dùng chung cho project "Dự đoán giá cổ phiếu VN-Index dựa trên biến
động giá trong quá khứ" (HCMUTE - Học Máy).

Phương pháp (đã hiệu chỉnh sau thí nghiệm đa horizon):
    Dự đoán 1 ngày bị nhiễu áp đảo (DirAcc ~50 %, phù hợp dạng yếu EMH).
    Vì vậy nhóm chọn **horizon trung hạn = 20 phiên (~ 1 tháng giao dịch)**
    làm target chính — đây là khung phổ biến của các chiến lược swing-trading
    và là khung mà tín hiệu xu hướng vượt mức ngẫu nhiên có ý nghĩa thống kê.

    Mục tiêu cụ thể:
        r_{t+h} = log( C_{t+h} / C_t ),  h = 20 (mặc định)
        Khôi phục giá: C_pred_{t+h} = C_t * exp(r_pred)

    Bộ 25 đặc trưng STATIONARY: lợi suất trễ (1..60), tỷ lệ với MA (5..100),
    volatility, RSI, MACD, Bollinger %b, biên độ ngày, biến động volume,
    trend (sign MA50-MA200).

Pipeline:
    1. Đọc dữ liệu (`load_raw_data`).
    2. Sinh đặc trưng (`build_features`).
    3. Chia chronological 80/20 (`time_series_split`).
    4. Huấn luyện 4 mô hình (LR, KNN, RF, Ensemble) — Pipeline với scaler.
    5. Đánh giá: MAE, RMSE, R², DirAcc, DirAcc_filt.
    6. So sánh đa horizon (`compare_horizons`).
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
# Đường dẫn mặc định
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "vcb_stock.csv"
IMAGE_DIR = PROJECT_ROOT / "image"
IMAGE_DIR.mkdir(exist_ok=True)


# Bộ đặc trưng STATIONARY mở rộng (25 đặc trưng)
FEATURE_COLUMNS: List[str] = [
    "Return_1", "Return_2", "Return_3", "Return_5", "Return_10", "Return_20", "Return_60",
    "MA5_Ratio", "MA10_Ratio", "MA20_Ratio", "MA50_Ratio", "MA100_Ratio",
    "Vol_5", "Vol_10", "Vol_20",
    "RSI_14",
    "MACD", "MACD_Signal", "MACD_Hist",
    "Bollinger_b",
    "HL_Range", "OC_Range",
    "Vol_Change", "Volume_MA20_Ratio",
    "Trend_MA50_200",
]
TARGET_COLUMN = "Target_Return"
PRICE_COLUMN = "Close"
DEFAULT_HORIZON = 20  # 20 phiên giao dịch ~ 1 tháng


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
# 2. Đặc trưng (feature engineering) — phiên bản mở rộng
# ----------------------------------------------------------------------
def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (rolling-mean smoothing)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def build_features(df: pd.DataFrame,
                   horizon: int = DEFAULT_HORIZON) -> pd.DataFrame:
    """Sinh 25 đặc trưng stationary + target = log-return h phiên tới.

    Tham số
    -------
    horizon : số phiên dự đoán về phía trước (mặc định 20 ≈ 1 tháng giao dịch).
    """
    out = df.copy()
    close = out["Close"]

    # Lợi suất trễ — multi-scale momentum
    for k in (1, 2, 3, 5, 10, 20, 60):
        out[f"Return_{k}"] = close.pct_change(k)

    # Tỷ lệ với MA — đa khung xu hướng
    for w in (5, 10, 20, 50, 100):
        out[f"MA{w}_Ratio"] = close / close.rolling(w).mean() - 1

    # Volatility (rolling std của lợi suất ngày)
    daily_ret = close.pct_change()
    for w in (5, 10, 20):
        out[f"Vol_{w}"] = daily_ret.rolling(w).std()

    # RSI
    out["RSI_14"] = _rsi(close, 14)

    # MACD-style (EMA12 - EMA26, signal EMA9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    out["MACD"] = macd_line / close
    out["MACD_Signal"] = macd_signal / close
    out["MACD_Hist"] = (macd_line - macd_signal) / close

    # Bollinger %b
    ma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    out["Bollinger_b"] = (close - (ma20 - 2 * std20)) / (4 * std20)

    # Biên độ trong phiên
    out["HL_Range"] = (out["High"] - out["Low"]) / close
    out["OC_Range"] = (out["Close"] - out["Open"]) / out["Open"]

    # Volume
    out["Vol_Change"] = out["Volume"].pct_change().replace([np.inf, -np.inf], np.nan)
    out["Volume_MA20_Ratio"] = out["Volume"] / out["Volume"].rolling(20).mean() - 1

    # Trend dài hạn (golden / death cross signal)
    out["Trend_MA50_200"] = np.sign(close.rolling(50).mean() - close.rolling(200).mean())

    # Target — log-return horizon ngày tới (smoother + symmetric hơn pct_change)
    out[TARGET_COLUMN] = np.log(close.shift(-horizon) / close)

    return out.dropna().reset_index(drop=True)


def get_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    return df[FEATURE_COLUMNS].copy(), df[TARGET_COLUMN].copy()


def time_series_split(X: pd.DataFrame, y: pd.Series,
                      train_ratio: float = 0.8
                      ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Chia tập theo trật tự thời gian (KHÔNG xáo trộn)."""
    split = int(len(X) * train_ratio)
    return X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]


# ----------------------------------------------------------------------
# 3. Mô hình
# ----------------------------------------------------------------------
def get_models(random_state: int = 42) -> Dict[str, object]:
    """Bốn mô hình — siêu tham số đã tinh chỉnh sơ bộ cho horizon=20."""
    lr = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression()),
    ])
    knn = Pipeline([
        ("scaler", StandardScaler()),
        ("model", KNeighborsRegressor(n_neighbors=25, weights="distance")),
    ])
    rf = RandomForestRegressor(
        n_estimators=500,
        max_depth=6,
        min_samples_leaf=20,
        max_features="sqrt",
        random_state=random_state,
        n_jobs=-1,
    )
    ensemble = VotingRegressor(estimators=[
        ("lr",  Pipeline([("scaler", StandardScaler()),
                          ("model", LinearRegression())])),
        ("knn", Pipeline([("scaler", StandardScaler()),
                          ("model", KNeighborsRegressor(n_neighbors=25,
                                                         weights="distance"))])),
        ("rf",  RandomForestRegressor(
            n_estimators=500, max_depth=6, min_samples_leaf=20,
            max_features="sqrt", random_state=random_state, n_jobs=-1)),
    ])
    return {
        "Linear Regression": lr,
        "KNN":               knn,
        "Random Forest":     rf,
        "Ensemble":          ensemble,
    }


def train_models(X_train: pd.DataFrame, y_train: pd.Series,
                 random_state: int = 42) -> Dict[str, object]:
    return {name: model.fit(X_train, y_train)
            for name, model in get_models(random_state).items()}


# ----------------------------------------------------------------------
# 4. Đánh giá
# ----------------------------------------------------------------------
def _diracc(y_true: np.ndarray, y_pred: np.ndarray,
            min_abs: float | None = None) -> float:
    """Direction accuracy. Nếu min_abs khác None thì chỉ tính trên mẫu có
    |y_true| >= min_abs (loại các phiên "đi ngang" không có chiều rõ)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if min_abs is not None:
        mask = np.abs(y_true) >= min_abs
        if not mask.any():
            return float("nan")
        y_true = y_true[mask]
        y_pred = y_pred[mask]
    st = np.sign(y_true);  st[st == 0] = 1
    sp = np.sign(y_pred);  sp[sp == 0] = 1
    return float((st == sp).mean() * 100.0)


def _metrics(y_true: pd.Series, y_pred: np.ndarray,
             diracc_threshold_q: float = 0.10) -> Dict[str, float]:
    """Bốn metric hồi quy + hai biến thể DirAcc."""
    y_true_arr = y_true.values if hasattr(y_true, "values") else np.asarray(y_true)
    rmse = float(np.sqrt(mean_squared_error(y_true_arr, y_pred)))
    mae = float(mean_absolute_error(y_true_arr, y_pred))
    r2 = float(r2_score(y_true_arr, y_pred))
    da_all = _diracc(y_true_arr, y_pred)
    thr = float(np.quantile(np.abs(y_true_arr), diracc_threshold_q))
    da_filt = _diracc(y_true_arr, y_pred, min_abs=thr)
    return {"MAE": mae, "RMSE": rmse, "R2": r2,
            "DirAcc(%)": da_all, "DirAcc_filt(%)": da_filt}


def evaluate_all(fitted: Dict[str, object],
                 X_test: pd.DataFrame, y_test: pd.Series
                 ) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    """Đánh giá trên miền log-return."""
    rows = []
    preds: Dict[str, np.ndarray] = {}
    for name, model in fitted.items():
        yhat = np.asarray(model.predict(X_test))
        preds[name] = yhat
        m = _metrics(y_test, yhat)
        m["Model"] = name
        rows.append(m)
    metrics = (pd.DataFrame(rows)
               .set_index("Model")[["MAE", "RMSE", "R2",
                                     "DirAcc(%)", "DirAcc_filt(%)"]]
               .round(4))
    return metrics, preds


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = np.abs(y_true) > 1e-9
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def to_price_predictions(close_today: pd.Series,
                         preds_logret: Dict[str, np.ndarray],
                         y_true_logret: pd.Series
                         ) -> Tuple[pd.Series, Dict[str, np.ndarray], pd.DataFrame]:
    """Chuyển log-return dự đoán thành giá: C_pred = C_t * exp(r_pred)."""
    close_today = close_today.reset_index(drop=True)
    y_true_price = close_today * np.exp(y_true_logret.reset_index(drop=True))
    preds_price: Dict[str, np.ndarray] = {
        name: (close_today.values * np.exp(p))
        for name, p in preds_logret.items()
    }
    rows = []
    for name, yp in preds_price.items():
        yt = y_true_price.values
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))
        mae = float(mean_absolute_error(yt, yp))
        mape = _safe_mape(yt, yp)
        rows.append({"Model": name,
                     "MAE (VND)": mae,
                     "RMSE (VND)": rmse,
                     "MAPE(%)": mape})
    return y_true_price, preds_price, pd.DataFrame(rows).set_index("Model").round(2)


# ----------------------------------------------------------------------
# 5. So sánh đa horizon
# ----------------------------------------------------------------------
def compare_horizons(horizons: List[int] = (1, 5, 10, 20, 60),
                     interval: str = "1d",
                     train_ratio: float = 0.8) -> pd.DataFrame:
    """Chạy pipeline trên nhiều khung dự đoán và trả bảng tổng hợp DirAcc."""
    raw = load_raw_data(interval=interval)
    rows = []
    for h in horizons:
        feat = build_features(raw, horizon=h)
        X, y = get_xy(feat)
        X_tr, X_te, y_tr, y_te = time_series_split(X, y, train_ratio)
        fitted = train_models(X_tr, y_tr)
        metrics, _ = evaluate_all(fitted, X_te, y_te)
        for name in metrics.index:
            rows.append({
                "Horizon": h,
                "Model": name,
                "DirAcc(%)": metrics.loc[name, "DirAcc(%)"],
                "DirAcc_filt(%)": metrics.loc[name, "DirAcc_filt(%)"],
                "MAE": metrics.loc[name, "MAE"],
                "R2": metrics.loc[name, "R2"],
            })
    return pd.DataFrame(rows).round(4)


# ----------------------------------------------------------------------
# 6. Trực quan
# ----------------------------------------------------------------------
def _save(fig: plt.Figure, save_path: os.PathLike | str | None) -> plt.Figure:
    if save_path is not None:
        fig.savefig(save_path, dpi=130, bbox_inches="tight")
    return fig


def plot_price_history(df: pd.DataFrame,
                       save_path: os.PathLike | str | None = None) -> plt.Figure:
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                              gridspec_kw={"height_ratios": [2.4, 1]})
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
    fig, ax = plt.subplots(figsize=(13, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
                cbar_kws={"shrink": .8}, annot_kws={"size": 7})
    ax.set_title("Ma trận tương quan: 25 đặc trưng + Target_Return (log, h=20)")
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
    """Biểu đồ cột so sánh các metric chính."""
    cols = [c for c in ["MAE", "RMSE", "R2", "DirAcc(%)", "DirAcc_filt(%)"]
            if c in metrics.columns]
    n = len(cols)
    fig, axes = plt.subplots(1, n, figsize=(3.0 * n, 4.4))
    if n == 1:
        axes = [axes]
    palette = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd"]
    direction = {"MAE": "thấp hơn = tốt hơn",
                 "RMSE": "thấp hơn = tốt hơn",
                 "R2": "cao hơn = tốt hơn",
                 "DirAcc(%)": "cao hơn = tốt hơn",
                 "DirAcc_filt(%)": "cao hơn = tốt hơn"}
    for ax, c in zip(axes, cols):
        ax.bar(metrics.index, metrics[c], color=palette[: len(metrics)])
        ax.set_title(f"{c}\n({direction[c]})", fontsize=10)
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", alpha=.3)
        if c.startswith("DirAcc"):
            ax.axhline(50, color="red", linestyle="--", alpha=.6, linewidth=1)
            ax.set_ylim(min(40, metrics[c].min() - 2), max(60, metrics[c].max() + 2))
        for i, v in enumerate(metrics[c]):
            ax.text(i, v, f"{v:.3g}", ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=8)
    fig.suptitle("So sánh hiệu năng các mô hình  (target = log-return 20 phiên)",
                 y=1.02, fontsize=12)
    fig.tight_layout()
    return _save(fig, save_path)


def plot_horizon_comparison(horizon_df: pd.DataFrame,
                            save_path: os.PathLike | str | None = None) -> plt.Figure:
    """Biểu đồ DirAcc theo từng horizon cho 4 mô hình."""
    pivot = horizon_df.pivot(index="Horizon", columns="Model",
                              values="DirAcc(%)")
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    palette = {"Linear Regression": "#1f77b4", "KNN": "#2ca02c",
               "Random Forest": "#d62728", "Ensemble": "#9467bd"}
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], marker="o", linewidth=2.0,
                color=palette.get(col, "#000"), label=col)
    ax.axhline(50, color="red", linestyle="--", alpha=.7, label="Ngẫu nhiên 50 %")
    ax.set_title("DirAcc theo khung dự đoán (horizon, phiên)")
    ax.set_xlabel("Horizon (số phiên dự đoán về phía trước)")
    ax.set_ylabel("DirAcc (%)")
    ax.set_xticks(sorted(pivot.index.unique()))
    ax.legend(loc="best"); ax.grid(alpha=.3)
    fig.tight_layout()
    return _save(fig, save_path)


# ----------------------------------------------------------------------
# 7. Pipeline đầy đủ
# ----------------------------------------------------------------------
def run_full_pipeline(interval: str = "1d",
                      horizon: int = DEFAULT_HORIZON,
                      train_ratio: float = 0.8,
                      save_images: bool = True) -> Dict[str, object]:
    """Chạy toàn bộ pipeline cho 1 horizon và trả về dict kết quả."""
    raw = load_raw_data(interval=interval)
    feat = build_features(raw, horizon=horizon)
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
            title=f"Dự đoán giá đóng cửa sau {horizon} phiên vs. Thực tế (VCB)",
            ylabel="Giá đóng cửa (VND)",
            save_path=IMAGE_DIR / "predictions_vs_actual.png",
        )
        plot_predictions_vs_actual(
            dates_test, y_te.values, preds_ret,
            title=f"Dự đoán log-return {horizon} phiên vs. Thực tế (VCB)",
            ylabel="Log-return",
            save_path=IMAGE_DIR / "returns_vs_actual.png",
        )

    return {
        "raw": raw, "features": feat,
        "horizon": horizon,
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
