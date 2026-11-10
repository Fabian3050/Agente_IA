"""
Módulo de Metodología Científica de Evaluación - Versión 3.0
Sección 5 de la Especificación Técnica:
- 5.1 Evaluación del Componente de Recuperación (Cobertura, Precisión, Error DOI).
- 5.2 Evaluación del Clasificador LLM y Acuerdo Inter-Evaluador:
  - Coeficiente Alfa de Krippendorff (α) para acuerdo inter-evaluador.
  - Precisión (P), Recall (R), F1-Score (Micro y Macro) con Intervalos de Confianza al 95% mediante remuestreo Bootstrap (1,000 iteraciones).
  - Medición de Estabilidad y Calibración a T=0.0 y T=0.3.
"""

import math
import random
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter


def krippendorff_alpha_nominal(matrix: List[List[Any]]) -> float:
    """
    Calcula el coeficiente Alfa de Krippendorff (α) para datos nominales.
    matrix: Lista de ítems (filas), donde cada fila contiene las etiquetas asignadas por cada evaluador (columnas).
    Si un evaluador no evaluó el ítem, el valor es None.
    """
    # 1. Recolectar todas las categorías únicas
    categories = set()
    for row in matrix:
        for val in row:
            if val is not None:
                categories.add(val)
    categories = list(categories)

    if not categories:
        return 0.0

    # 2. Construir la tabla de coincidencias coincidentes
    n_total = 0
    observed_pairs = 0
    pair_counts = Counter()
    marginal_counts = Counter()

    for row in matrix:
        valid_vals = [v for v in row if v is not None]
        m_i = len(valid_vals)
        if m_i > 1:
            n_total += m_i
            # Pares dentro del mismo ítem
            for j in range(m_i):
                for k in range(m_i):
                    if j != k:
                        pair_counts[(valid_vals[j], valid_vals[k])] += 1 / (m_i - 1)
        for v in valid_vals:
            marginal_counts[v] += 1

    total_pairs = sum(pair_counts.values())
    if total_pairs == 0:
        return 0.0

    # Desacuerdo observado (Do)
    disagreement_observed = 0.0
    for (c1, c2), count in pair_counts.items():
        if c1 != c2:
            disagreement_observed += count

    # Desacuerdo esperado por azar (De)
    total_marginal = sum(marginal_counts.values())
    if total_marginal <= 1:
        return 0.0

    disagreement_expected = 0.0
    for c1 in categories:
        for c2 in categories:
            if c1 != c2:
                p_c1 = marginal_counts[c1]
                p_c2 = marginal_counts[c2]
                disagreement_expected += (p_c1 * p_c2) / (total_marginal - 1)

    if disagreement_expected == 0.0:
        return 1.0

    alpha = 1.0 - (disagreement_observed / disagreement_expected)
    return round(alpha, 4)


def compute_classification_metrics(
    y_true: List[List[str]],
    y_pred: List[List[str]]
) -> Dict[str, float]:
    """
    Calcula métricas multietiqueta: Precisión, Recall y F1-Score (Micro y Macro).
    """
    # Micro Métricas
    total_tp = 0
    total_fp = 0
    total_fn = 0

    all_labels = set()
    for labels in y_true + y_pred:
        all_labels.update(labels)

    per_label_metrics = {}

    for label in all_labels:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if label in yt and label in yp)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if label not in yt and label in yp)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if label in yt and label not in yp)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        per_label_metrics[label] = {"p": p, "r": r, "f1": f1}

    # Micro
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2 * micro_p * micro_r) / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    # Macro
    if all_labels:
        macro_p = sum(m["p"] for m in per_label_metrics.values()) / len(all_labels)
        macro_r = sum(m["r"] for m in per_label_metrics.values()) / len(all_labels)
        macro_f1 = sum(m["f1"] for m in per_label_metrics.values()) / len(all_labels)
    else:
        macro_p = macro_r = macro_f1 = 0.0

    return {
        "micro_precision": round(micro_p, 4),
        "micro_recall": round(micro_r, 4),
        "micro_f1": round(micro_f1, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
    }


def bootstrap_f1_ci(
    y_true: List[List[str]],
    y_pred: List[List[str]],
    n_iterations: int = 1000,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Calcula Intervalos de Confianza al 95% para F1-Score (Micro y Macro)
    mediante Remuestreo con Reemplazo (Bootstrap, 1,000 iteraciones).
    Sección 5.2 de la Especificación Técnica.
    """
    n = len(y_true)
    if n == 0:
        return {}

    micro_f1_samples = []
    macro_f1_samples = []

    random.seed(42)  # Semilla para reproducibilidad científica

    for _ in range(n_iterations):
        # Muestreo con reemplazo
        indices = [random.randint(0, n - 1) for _ in range(n)]
        yt_sample = [y_true[i] for i in indices]
        yp_sample = [y_pred[i] for i in indices]

        metrics = compute_classification_metrics(yt_sample, yp_sample)
        micro_f1_samples.append(metrics["micro_f1"])
        macro_f1_samples.append(metrics["macro_f1"])

    micro_f1_samples.sort()
    macro_f1_samples.sort()

    lower_idx = int(((1.0 - confidence_level) / 2.0) * n_iterations)
    upper_idx = int((confidence_level + (1.0 - confidence_level) / 2.0) * n_iterations) - 1

    base_metrics = compute_classification_metrics(y_true, y_pred)

    return {
        "base_metrics": base_metrics,
        "n_iterations": n_iterations,
        "confidence_level": confidence_level,
        "micro_f1_ci_95": (
            round(micro_f1_samples[lower_idx], 4),
            round(micro_f1_samples[upper_idx], 4)
        ),
        "macro_f1_ci_95": (
            round(macro_f1_samples[lower_idx], 4),
            round(macro_f1_samples[upper_idx], 4)
        )
    }

