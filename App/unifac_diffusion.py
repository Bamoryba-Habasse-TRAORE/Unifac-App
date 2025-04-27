import math

# --- Données UNIFAC des composés (groupes + nombres) ---
compounds = {"Propylene": {"groups": {"CH3": 1, "CH2=CH": 1}},"Benzene": {"groups": {"ACH": 6}},"Acetaldehyde": {"groups": {"CH3": 1, "HCO": 1}},"MethylEthylamine": {"groups": {"CH3": 2, "CH2NH": 1}},
    # Ajout de l'éthanol, du toluène et de l'eau
"Ethanol": {"groups": {"CH3": 1, "CH2": 1, "OH": 1}},"Toluene":{"groups": {"CH3": 1, "ACH": 5, "AC": 1}},"Water": {"groups": {"OH": 1}},}
# --- Paramètres r (volume) et q (surface) pour chaque groupe ---
groups = {"CH3": {"R": 0.9011, "Q": 0.848},"CH2": {"R": 0.6744, "Q": 0.540},"CH2=CH": {"R": 1.3454, "Q": 1.176},"ACH": {"R": 0.5313, "Q": 0.400},"HCO": {"R": 0.9980, "Q": 0.948},"CH2NH":  {"R": 1.2070, "Q": 0.936},
    # Nouveaux groupes
"OH": {"R": 0.9200, "Q": 1.4000}, "AC": {"R": 0.4000, "Q": 0.2280}, }

# --- Paramètres d'interaction a_ij (K) simplifiés ---
interactions = {("CH3", "CH2=CH"): 986.5,("CH3", "ACH"):    476.4,("CH3", "HCO"):    663.5,("CH3", "CH2NH"):  335.8,("CH2=CH", "ACH"): 84.0,("CH2=CH", "HCO"): 199.0,("CH2=CH", "CH2NH"): 313.5,("ACH", "HCO"):    669.4,("ACH", "CH2NH"):  53.59,("HCO", "CH2NH"):  228.4,
    # Interactions pour OH (eau)
    ("OH", "CH3"):     1500.0,("OH", "CH2"):     1400.0,("OH", "CH2=CH"):  1300.0,("OH", "ACH"):     1700.0,("OH", "HCO"):     600.0,("OH", "CH2NH"):   500.0,
    # Interactions pour AC (toluène)
    ("AC", "CH3"):     500.0,("AC", "ACH"):     200.0,}

def list_available_compounds():
    """
    Retourne la liste des composés disponibles dans l'application.
    """
    return list(compounds.keys())

# Récupère le paramètre d'interaction a_ij entre deux groupes
def get_aij(g1, g2):
    return interactions.get((g1, g2)) or interactions.get((g2, g1), 0.0)

# Calcule r et q d'un composé à partir de sa décomposition en groupes
def compute_RQ(comp):
    r = q = 0.0
    for g, n in comp.items():
        if g not in groups:
            raise ValueError(f"Paramètres UNIFAC manquants pour le groupe '{g}'.")
        r += n * groups[g]["R"]
        q += n * groups[g]["Q"]
    return r, q

# Calcule lnγ combinatoire et résiduel
def compute_comb_and_res(x1, x2, comp1, comp2, T):
    r1, q1 = compute_RQ(comp1)
    r2, q2 = compute_RQ(comp2)
    sum_r = x1 * r1 + x2 * r2
    sum_q = x1 * q1 + x2 * q2
    phi1 = x1 * r1 / sum_r
    phi2 = x2 * r2 / sum_r
    theta1 = x1 * q1 / sum_q
    theta2 = x2 * q2 / sum_q

    ln_gamma_comb_1 = (1 - phi1) + math.log(phi1) - 5 * q1 * (1 - theta1/phi1 + math.log(theta1/phi1))
    ln_gamma_comb_2 = (1 - phi2) + math.log(phi2) - 5 * q2 * (1 - theta2/phi2 + math.log(theta2/phi2))

    # Calcul du résiduel
    groups_mix = set(comp1) | set(comp2)
    tau = {(gi, gj): math.exp(-get_aij(gi, gj) / T) for gi in groups_mix for gj in groups_mix}
    Q_mix = sum((comp1.get(g, 0) * x1 + comp2.get(g, 0) * x2) * groups[g]["Q"] for g in groups_mix)
    theta_mix = {g: (comp1.get(g, 0) * x1 + comp2.get(g, 0) * x2) * groups[g]["Q"] / Q_mix for g in groups_mix}

    def ln_gamma_res(comp):
        val = 0.0
        for g in comp:
            sum1 = sum(theta_mix[k] * tau[(k, g)] for k in groups_mix)
            sum2 = sum(theta_mix[k] * tau[(g, k)] for k in groups_mix)
            val += comp[g] * groups[g]["Q"] * (1 - math.log(sum1) - sum2/sum1)
        return val

    return ln_gamma_comb_1 + ln_gamma_res(comp1), ln_gamma_comb_2 + ln_gamma_res(comp2)

# Coefficient de diffusion selon UNIFAC
def unifac_diffusion(comp1_name, comp2_name, x1, T, D_exp=None):
    """
    Calcule le coefficient de diffusion et, optionnellement, l'erreur relative.
    Lève ValueError si les composés ne sont pas disponibles ou en cas de paramètres manquants.
    """
    # Validation des noms de composés
    if comp1_name not in compounds or comp2_name not in compounds:
        raise ValueError(f"Choix invalide: '{comp1_name}' ou '{comp2_name}' n'est pas défini."
                         f" Options possibles: {list_available_compounds()}")
    x2 = 1 - x1
    try:
        comp1 = compounds[comp1_name]["groups"]
        comp2 = compounds[comp2_name]["groups"]
        ln_g1, ln_g2 = compute_comb_and_res(x1, x2, comp1, comp2, T)
    except ValueError as e:
        raise ValueError(f"Erreur UNIFAC: {e}")

    ln_D = (1 - x1) * ln_g1 + x1 * ln_g2
    D = math.exp(ln_D) * 1e-6
    error_pct = None
    if D_exp is not None:
        if D_exp == 0:
            raise ValueError("D_exp ne peut pas être zéro pour le calcul de l'erreur")
        error_pct = abs(D_exp - D) / D_exp * 100
    return D, error_pct
