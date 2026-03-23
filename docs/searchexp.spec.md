# Spécification formelle — Recherche par expression

Grammaire du mini-langage de recherche par expression de Pysaurus.
Notation EBNF. Voir `docs/searchexp.design.md` pour les décisions de conception
et les questions ouvertes.

## 1. Grammaire lexicale (tokens)

### Espaces

```ebnf
WS = (" " | "\t" | "\r" | "\n")+ ;
```

Les espaces séparent les tokens mais ne sont pas significatifs.

### Mots-clés (insensibles à la casse)

```ebnf
AND      = "and" ;
OR       = "or" ;
XOR      = "xor" ;
NOT      = "not" ;
IN       = "in" ;
IS       = "is" ;
TRUE     = "True" ;
FALSE    = "False" ;
LEN      = "len" ;
```

Insensibles à la casse : `AND` ≡ `and` ≡ `And`.

Les mots-clés ne peuvent pas être utilisés comme noms d'attributs.

### Identifiants

```ebnf
IDENT    = LETTER (LETTER | DIGIT | "_")* ;
LETTER   = "a"..."z" | "A"..."Z" | "_" ;
DIGIT    = "0"..."9" ;
```

Sensibles à la casse. Désignent les attributs vidéo (`width`, `found`, etc.).
Un identifiant qui correspond à un mot-clé est interprété comme mot-clé.

### Propriétés custom

```ebnf
PROPERTY = "`" PROP_CHAR+ "`" ;
PROP_CHAR = ? tout caractère sauf "`" ? ;
```

Le contenu entre accents graves est le nom de la propriété, tel quel.

### Littéraux numériques

```ebnf
NUMBER       = INT_PART FRAC_PART? MULTIPLIER? ;
INT_PART     = DIGIT+ ;
FRAC_PART    = "." DIGIT+ ;
MULTIPLIER   = "k" | "m" | "g" | "t" | "ki" | "mi" | "gi" | "ti" ;
```

Insensible à la casse pour le multiplicateur.

- Sans partie fractionnaire ni multiplicateur : `int`
- Avec partie fractionnaire ou multiplicateur produisant un non-entier : `float`
- Le multiplicateur applique un facteur :
  base 1000 (`k` = ×1 000, `m` = ×1 000 000, `g` = ×10⁹, `t` = ×10¹²),
  base 1024 (`ki` = ×1 024, `mi` = ×1 048 576, `gi` = ×1 073 741 824,
  `ti` = ×1 099 511 627 776)

### Littéraux durée

```ebnf
DURATION        = DURATION_PART+ ;
DURATION_PART   = DIGIT+ DURATION_SUFFIX ;
DURATION_SUFFIX = "d" | "h" | "min" | "s" | "u" ;
```

Insensible à la casse pour les suffixes.

Contraintes (vérifiées après tokenisation) :
- Les composants doivent être en ordre décroissant de précision :
  `d` > `h` > `min` > `s` > `u`
- Chaque suffixe apparaît au plus une fois
- Au moins un composant requis

Exemples valides : `5min30s`, `1h25min`, `2d5h`, `45s`, `10min500u`

Note : la distinction avec NUMBER + MULTIPLIER se fait par le suffixe.
`5min` = durée (suffixe `min`), `5mi` = nombre × 1 048 576 (suffixe `mi`),
`5m` = nombre × 1 000 000 (suffixe `m`). Le tokenizer matche le suffixe
le plus long en priorité.

### Littéraux date

```ebnf
DATE         = YEAR ("-" MONTH ("-" DAY ("T" HOUR (":" MINUTE (":" SECOND)?)?)?)?)? ;
YEAR         = DIGIT DIGIT DIGIT DIGIT ;
MONTH        = DIGIT DIGIT ;
DAY          = DIGIT DIGIT ;
HOUR         = DIGIT DIGIT ;
MINUTE       = DIGIT DIGIT ;
SECOND       = DIGIT DIGIT ;
```

Séparateur `T` (ISO 8601) entre la date et l'heure.

6 niveaux de précision :
1. `YYYY` — année
2. `YYYY-MM` — mois
3. `YYYY-MM-DD` — jour
4. `YYYY-MM-DDTHH` — heure
5. `YYYY-MM-DDTHH:MM` — minute
6. `YYYY-MM-DDTHH:MM:SS` — seconde

Note : `YYYY` seul (ex. `2024`) est ambigu avec un entier. La résolution
se fait lors de la passe de typage, selon le type du champ associé.

### Littéraux chaîne

```ebnf
STRING       = DQ_STRING | SQ_STRING ;
DQ_STRING    = '"' DQ_CHAR* '"' ;
SQ_STRING    = "'" SQ_CHAR* "'" ;
DQ_CHAR      = ? tout caractère sauf '"' ? ;
SQ_CHAR      = ? tout caractère sauf "'" ? ;
```

Pas de séquences d'échappement en v1.

### Opérateurs et ponctuation

```ebnf
EQ       = "==" ;
NEQ      = "!=" ;
LTE      = "<=" ;
GTE      = ">=" ;
LT       = "<" ;
GT       = ">" ;
LPAREN   = "(" ;
RPAREN   = ")" ;
LBRACE   = "{" ;
RBRACE   = "}" ;
COMMA    = "," ;
```

### Priorité de tokenisation

Quand plusieurs règles lexicales matchent, le tokenizer utilise :
1. Match le plus long en priorité (maximal munch)
2. À longueur égale : mots-clés > identifiants

## 2. Grammaire syntaxique (expressions)

La grammaire encode la priorité des opérateurs directement dans les
règles de production (du moins prioritaire au plus prioritaire).

```ebnf
expression     = or_expr ;

or_expr        = xor_expr (OR xor_expr)* ;

xor_expr       = and_expr (XOR and_expr)* ;

and_expr       = not_expr (AND not_expr)* ;

not_expr       = NOT not_expr
               | comparison ;

comparison     = operand (comp_op operand)?
               | operand IS boolean
               | boolean IS operand
               | operand NOT IN operand
               | operand IN operand ;

comp_op        = EQ | NEQ | LT | LTE | GT | GTE ;

operand        = function_call
               | atom ;

function_call  = LEN LPAREN operand RPAREN ;

atom           = IDENT
               | PROPERTY
               | literal
               | LPAREN expression RPAREN ;

literal        = NUMBER
               | DURATION
               | DATE
               | STRING
               | boolean
               | set_literal ;

boolean        = TRUE | FALSE ;

set_literal    = LBRACE RBRACE
               | LBRACE literal (COMMA literal)* COMMA? RBRACE ;
```

Notes :
- Une seule comparaison par expression (pas de chaînage `a < b < c`).
- `NOT IN` est un opérateur composé de deux mots-clés, pas `NOT` suivi de `IN`.
- `IS` ne s'applique qu'entre un opérande et un booléen.
- Un `operand` seul est valide comme expression (ex. `found` → évalué comme booléen).

## 3. Contrainte sémantique : littéral vs littéral

Pour tout opérateur binaire (comparaison, `IN`, `IS`), au moins un des
deux opérandes doit être un champ (identifiant, propriété, ou appel de
fonction). Les expressions littéral-vs-littéral sont rejetées.

Cette contrainte est vérifiée après le parsing syntaxique, lors de la
passe de typage.

## 4. Règles de typage

### Types du langage

| Type | Valeur interne |
|------|---------------|
| `bool` | `bool` |
| `int` | `int` |
| `float` | `float` |
| `str` | `str` |
| `Date` | `float` (timestamp) |
| `Duration` | `int` (microsecondes) |
| `FileSize` | `int` (octets) |
| `set[T]` | ensemble de `T` |

### Résolution des littéraux ambigus

Un littéral `NUMBER` qui ne contient ni partie fractionnaire ni multiplicateur
(ex. `2024`) est ambigu : `int`, `float`, `Date`, `Duration`, ou `FileSize`
selon le contexte. Le type est résolu par le champ de l'autre côté de
l'opérateur.

### Opérateurs par type

| Opérateur | Types autorisés |
|-----------|----------------|
| `==`, `!=` | tous |
| `<`, `<=`, `>`, `>=` | `int`, `float`, `str`, `Date`, `Duration`, `FileSize` |
| `is` | `bool` uniquement |
| `in` (sous-chaîne) | `str` in `str` |
| `in` (appartenance) | `T` in `set[T]` (tout type `T`) |
| `len()` | `str`, `set[T]` → `int` |

### Compatibilités croisées

| Croisement | Autorisé |
|-----------|----------|
| `int` ↔ `float` | oui |
| `FileSize` ↔ `int`, `float` | oui |
| `Duration` ↔ `int`, `float` | oui |
| `Date` ↔ `int`, `float` | oui |
| `FileSize` ↔ `Duration` | non |
| `FileSize` ↔ `Date` | non |
| `Duration` ↔ `Date` | non |

### Opérateurs logiques

`and`, `or`, `xor` : les deux opérandes doivent être des expressions
booléennes (comparaisons, appels à `is`, expressions `in`, ou champs
`bool` seuls).

`not` : l'opérande doit être une expression booléenne.
