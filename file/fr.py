import pprint
import re

from utils.file.yyaml import save_yaml
from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wl, wlexpr




GAUGE_PARAMS="""
  aEWM1 == { 
    ParameterType    -> External, 
    BlockName        -> SMINPUTS, 
    OrderBlock       -> 1, 
    Value            -> 127.9,
    InteractionOrder -> {QED,-2},
    Description      -> "Inverse of the EW coupling constant at the Z pole"
  },
  Gf == {
    ParameterType    -> External,
    BlockName        -> SMINPUTS,
    OrderBlock       -> 2,
    Value            -> 1.16637*^-5, 
    InteractionOrder -> {QED,2},
    TeX              -> Subscript[G,f],
    Description      -> "Fermi constant"
  },
  aS    == { 
    ParameterType    -> External,
    BlockName        -> SMINPUTS,
    OrderBlock       -> 3,
    Value            -> 0.1184, 
    InteractionOrder -> {QCD,2},
    TeX              -> Subscript[\[Alpha],s],
    Description      -> "Strong coupling constant at the Z pole"
  },
  ymdo == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 1,
    Value         -> 5.04*^-3,
    Description   -> "Down Yukawa mass"
  },
  ymup == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 2,
    Value         -> 2.55*^-3,
    Description   -> "Up Yukawa mass"
  },
  yms == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 3,
    Value         -> 0.101,
    Description   -> "Strange Yukawa mass"
  },
  ymc == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 4,
    Value         -> 1.27,
    Description   -> "Charm Yukawa mass"
  },
  ymb == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 5,
    Value         -> 4.7,
    Description   -> "Bottom Yukawa mass"
  },
  ymt == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 6,
    Value         -> 172,
    Description   -> "Top Yukawa mass"
  },
  yme == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 11,
    Value         -> 5.11*^-4,
    Description   -> "Electron Yukawa mass"
  },
  ymm == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 13,
    Value         -> 0.10566,
    Description   -> "Muon Yukawa mass"
  },
  ymtau == {
    ParameterType -> External,
    BlockName     -> YUKAWA,
    OrderBlock    -> 15,
    Value         -> 1.777,
    Description   -> "Tau Yukawa mass"
  },
  cabi == {
    ParameterType -> External,
    BlockName     -> CKMBLOCK,
    OrderBlock    -> 1,
    Value         -> 0.227736,
    TeX           -> Subscript[\[Theta], c],
    Description   -> "Cabibbo angle"
  },

  (* Internal Parameters *)
  aEW == {
    ParameterType    -> Internal,
    Value            -> 1/aEWM1,
    InteractionOrder -> {QED,2},
    TeX              -> Subscript[\[Alpha], EW],
    Description      -> "Electroweak coupling contant"
  },
  MW == { 
    ParameterType -> Internal, 
    Value         -> Sqrt[MZ^2/2+Sqrt[MZ^4/4-Pi/Sqrt[2]*aEW/Gf*MZ^2]], 
    TeX           -> Subscript[M,W], 
    Description   -> "W mass"
  },
  sw2 == { 
    ParameterType -> Internal, 
    Value         -> 1-(MW/MZ)^2, 
    Description   -> "Squared Sin of the Weinberg angle"
  },
  ee == { 
    ParameterType    -> Internal, 
    Value            -> Sqrt[4 Pi aEW], 
    InteractionOrder -> {QED,1}, 
    TeX              -> e,  
    Description      -> "Electric coupling constant"
  },
  cw == { 
    ParameterType -> Internal, 
    Value         -> Sqrt[1-sw2], 
    TeX           -> Subscript[c,w], 
    Description   -> "Cosine of the Weinberg angle"
  },
  sw == { 
    ParameterType -> Internal, 
    Value         -> Sqrt[sw2], 
    TeX           -> Subscript[s,w], 
    Description   -> "Sine of the Weinberg angle"
  },
  gw == { 
    ParameterType    -> Internal, 
    Definitions      -> {gw->ee/sw}, 
    InteractionOrder -> {QED,1},  
    TeX              -> Subscript[g,w], 
    Description      -> "Weak coupling constant at the Z pole"
  },
  g1 == { 
    ParameterType    -> Internal, 
    Definitions      -> {g1->ee/cw}, 
    InteractionOrder -> {QED,1},  
    TeX              -> Subscript[g,1], 
    Description      -> "U(1)Y coupling constant at the Z pole"
  },
  gs == { 
    ParameterType    -> Internal, 
    Value            -> Sqrt[4 Pi aS],
    InteractionOrder -> {QCD,1},  
    TeX              -> Subscript[g,s], 
    ParameterName    -> G,
    Description      -> "Strong coupling constant at the Z pole"
  },
  vev == {
    ParameterType    -> Internal,
    Value            -> 2*MW*sw/ee, 
    InteractionOrder -> {QED,-1},
    Description      -> "Higgs vacuum expectation value"
  },
  lam == {
    ParameterType    -> Internal,
    Value            -> MH^2/(2*vev^2),
    InteractionOrder -> {QED, 2},
    Description      -> "Higgs quartic coupling"
  },
  muH == {
    ParameterType -> Internal,
    Value         -> Sqrt[vev^2 lam],
    TeX           -> \[Mu],
    Description   -> "Coefficient of the quadratic piece of the Higgs potential"
  },
  yl == {
    ParameterType    -> Internal,
    Indices          -> {Index[Generation], Index[Generation]},
    Definitions      -> {yl[i_?NumericQ, j_?NumericQ] :> 0  /; (i =!= j)},
    Value            -> {yl[1,1] -> Sqrt[2] yme / vev, yl[2,2] -> Sqrt[2] ymm / vev, yl[3,3] -> Sqrt[2] ymtau / vev},
    InteractionOrder -> {QED, 1},
    ParameterName    -> {yl[1,1] -> ye, yl[2,2] -> ym, yl[3,3] -> ytau},
    TeX              -> Superscript[y, l],
    Description      -> "Lepton Yukawa couplings"
  },
  yu == {
    ParameterType    -> Internal,
    Indices          -> {Index[Generation], Index[Generation]},
    Definitions      -> {yu[i_?NumericQ, j_?NumericQ] :> 0  /; (i =!= j)},
    Value            -> {yu[1,1] -> Sqrt[2] ymup/vev, yu[2,2] -> Sqrt[2] ymc/vev, yu[3,3] -> Sqrt[2] ymt/vev},
    InteractionOrder -> {QED, 1},
    ParameterName    -> {yu[1,1] -> yup, yu[2,2] -> yc, yu[3,3] -> yt},
    TeX              -> Superscript[y, u],
    Description      -> "Up-type Yukawa couplings"
  },
  yd == {
    ParameterType    -> Internal,
    Indices          -> {Index[Generation], Index[Generation]},
    Definitions      -> {yd[i_?NumericQ, j_?NumericQ] :> 0  /; (i =!= j)},
    Value            -> {yd[1,1] -> Sqrt[2] ymdo/vev, yd[2,2] -> Sqrt[2] yms/vev, yd[3,3] -> Sqrt[2] ymb/vev},
    InteractionOrder -> {QED, 1},
    ParameterName    -> {yd[1,1] -> ydo, yd[2,2] -> ys, yd[3,3] -> yb},
    TeX              -> Superscript[y, d],
    Description      -> "Down-type Yukawa couplings"
  },

"""
LEX_URL = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\physics\quantum_fields\equations\FSM\fsm_lexicon.yaml"
import re

def parse_matrix_param(entry):
    name_match = re.search(r'^(\w+)\s*==', entry)
    if not name_match:
        return None
    name = name_match.group(1)

    desc_match = re.search(r'Description\s*->\s*"([^"]+)"', entry)
    desc = desc_match.group(1) if desc_match else ""

    # Werte extrahieren
    value_match = re.findall(r'\[(\d),(\d)\]\s*->\s*([^,{}]+)', entry)
    values = {(int(i), int(j)): expr.strip() for i, j, expr in value_match}

    # Symbolnamen extrahieren
    symbol_match = re.findall(r'\[(\d),(\d)\]\s*->\s*(\w+)', entry.split("ParameterName")[1])
    symbols = {(int(i), int(j)): name for i, j, name in symbol_match}

    return {
        "type": "matrix",
        "description": desc,
        "symbol": name,
        "value": values,
        "parameter_names": symbols,
        "zeros_offdiag": "i =!= j" in entry,
        "origin": "derived" if "internal" in entry.lower() else "measured"
    }




if __name__ == "__main__":
    full_parameters_yaml = parse_matrix_param(GAUGE_PARAMS)


    save_yaml(filepath=LEX_URL, data=full_parameters_yaml)

