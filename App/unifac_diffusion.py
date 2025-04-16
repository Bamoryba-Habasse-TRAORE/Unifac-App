import math

# Données UNIFAC des composés (groupes + nombres)
compounds = {"Propylene": {"groups": {"CH3": 1, "CH2=CH": 1}},"Benzene": {"groups": {"ACH": 6}},"Acetaldehyde": {"groups": {"CH3": 1, "HCO": 1}},"MethylEthylamine": {"groups": {"CH3": 2, "CH2NH": 1}},}
# Paramètres R et Q pour les groupes
groups = {"CH3": {"R": 0.9011, "Q": 0.848}, "CH2": {"R": 0.6744, "Q": 0.540},"CH2=CH": {"R": 1.3454, "Q": 1.176},"ACH": {"R": 0.5313, "Q": 0.400},"HCO": {"R": 0.998, "Q": 0.948},"CH2NH": {"R": 1.207, "Q": 0.936}}
# Interactions simplifiées a_ij (K)
interactions = {("CH3", "CH2=CH"): 986.5,("CH3", "ACH"): 476.4,("CH3", "HCO"): 663.5,("CH3", "CH2NH"): 335.8,("CH2=CH", "ACH"): 84,("CH2=CH", "HCO"): 199,("CH2=CH", "CH2NH"): 313.5,("ACH", "HCO"): 669.4,("ACH", "CH2NH"): 53.59,("HCO", "CH2NH"): 228.4,}
def get_aij(g1, g2):
    return interactions.get((g1, g2)) or interactions.get((g2, g1), 0)
def compute_RQ(comp):
    R = Q = 0
    for g, count in comp.items():
        R += count * groups[g]["R"]
        Q += count * groups[g]["Q"]
    return R, Q
def compute_comb_and_res(x1, x2, comp1, comp2, T):
    R1, Q1 = compute_RQ(comp1)
    R2, Q2 = compute_RQ(comp2)
    l1, l2 = R1 ** (1/3), R2 ** (1/3)
    phi1 = (x1 * l1) / (x1 * l1 + x2 * l2)
    phi2 = (x2 * l2) / (x1 * l1 + x2 * l2)
    theta1 = (x1 * Q1) / (x1 * Q1 + x2 * Q2)
    theta2 = (x2 * Q2) / (x1 * Q1 + x2 * Q2)
    ln_gamma_comb_1 = math.log(phi1 / x1) + 5 * Q1 * math.log(theta1 / phi1) + phi2 - phi1
    ln_gamma_comb_2 = math.log(phi2 / x2) + 5 * Q2 * math.log(theta2 / phi2) + phi1 - phi2
    all_groups = set(comp1.keys()) | set(comp2.keys())
    tau = {(g1, g2): math.exp(-get_aij(g1, g2)/T) if get_aij(g1, g2) else 1.0 for g1 in all_groups for g2 in all_groups}
    Q_vals = {g: groups[g]["Q"] for g in all_groups}
    theta_mix = {}
    total = sum((comp1.get(g, 0) * x1 + comp2.get(g, 0) * x2) * Q_vals[g] for g in all_groups)
    for g in all_groups:
        theta_mix[g] = (comp1.get(g, 0) * x1 + comp2.get(g, 0) * x2) * Q_vals[g] / total
    def ln_gamma_res(comp):
        res = 0
        for g in comp:
            sum1 = sum(theta_mix[k] * tau[(k, g)] for k in all_groups)
            sum2 = sum(theta_mix[k] * tau[(g, k)] for k in all_groups)
            res += comp[g] * Q_vals[g] * (1 - math.log(sum1) - sum2 / sum1)
        return res
    ln_gamma1 = ln_gamma_comb_1 + ln_gamma_res(comp1)
    ln_gamma2 = ln_gamma_comb_2 + ln_gamma_res(comp2)
    return ln_gamma1, ln_gamma2
def unifac_diffusion(compound1, compound2, x1, T, D_exp=None):
    if compound1 not in compounds or compound2 not in compounds:
        raise ValueError("Composé inconnu")
    x2 = 1 - x1
    comp1 = compounds[compound1]["groups"]
    comp2 = compounds[compound2]["groups"]
    ln_g1, ln_g2 = compute_comb_and_res(x1, x2, comp1, comp2, T)
    ln_D = (1 - x1) * ln_g1 + x1 * ln_g2
    D = math.exp(ln_D) * 1e-6 # Coefficient empirique de base
    error = None
    if D_exp:
        error = abs(D_exp - D) / D_exp * 100
    return D, error
