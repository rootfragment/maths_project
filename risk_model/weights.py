import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.decomposition import PCA

from .config import FACTOR_KEYS

def derive_weights_regression(all_data, min_usable=5):

    usable = [d for d in all_data if not np.isnan(d["future_mdd"])]
    if len(usable) < min_usable:
        raise RuntimeError(
            f"Only {len(usable)} stocks have a valid future window; "
            f"need at least {min_usable} to derive regression weights."
        )

    X = np.array([[d["scores"][f] for f in FACTOR_KEYS] for d in usable])
    y = np.array([d["future_mdd"] for d in usable])

    alphas = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0]
    model = RidgeCV(alphas=alphas)
    model.fit(X, y)

    coefs = np.abs(model.coef_)
    if coefs.sum() == 0:
        coefs = np.ones(len(FACTOR_KEYS))
    weights = coefs / coefs.sum()
    print(f"  RidgeCV chose alpha={model.alpha_}")
    return dict(zip(FACTOR_KEYS, weights.round(3)))

def derive_weights_pca(all_data):

    X = np.array([[d["scores"][f] for f in FACTOR_KEYS] for d in all_data])
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)

    pca = PCA(n_components=1)
    pca.fit(X)
    loadings = np.abs(pca.components_[0])
    weights = loadings / loadings.sum()
    return dict(zip(FACTOR_KEYS, weights.round(3)))

def blend_weights(weights_regression, weights_pca):

    blended = {
        f: (weights_regression[f] + weights_pca[f]) / 2
        for f in FACTOR_KEYS
    }
    total = sum(blended.values())
    return {f: round(w / total, 3) for f, w in blended.items()}
