# fbg-force-sleeve

Une étude de conception ouverte pour un **manchon à clipser, avec quatre fibres optiques**, qui pourrait mesurer la **force latérale sur la tige** d'un instrument de laparoscopie manuel, et la séparer de la chaleur de l'électrochirurgie.

> **Usage de recherche uniquement. Ce n'est pas un dispositif médical. Aucun capteur n'a été construit ni testé.**
> Tout ce qui est dans `results/` vient d'une simulation à paramètres supposés. Cela montre comment la méthode se comporte dans un modèle, pas qu'un manchon construit fonctionne.

English: [README.md](README.md)

## L'idée en une minute

- Un réseau de Bragg (FBG) est un motif gravé dans une fibre optique, qui renvoie une couleur précise. La couleur change quand la fibre s'étire, et aussi quand elle chauffe.
- Trois fibres sont collées sur la tige, à 120° les unes des autres : elles sentent la flexion et la chaleur. Une quatrième repose librement contre la tige et ne sent que la chaleur : c'est le thermomètre.
- Quatre lectures donnent quatre inconnues : la force dans deux directions latérales, la force le long de la tige, et la température. Sans la fibre-thermomètre, la matrice perd un rang et le code refuse de calculer.
- Le manchon est une pince imprimée en 3D qui tient les fibres contre la tige. Il ne mesure rien lui-même. Les fibres sortent du manchon en un câble fin vers un appareil de lecture.

## Ce que montre la simulation (tige de 5 mm, paramètres supposés)

| Question | Résultat |
|---|---|
| Plus petite variation de force latérale au-dessus du bruit | environ 1 g avec un lecteur de laboratoire (1 pm), environ 3 g avec un lecteur bon marché (3 pm). Cible des articles : 38 g (0,375 N) |
| Force le long de la tige | Illisible avec un simple tube : environ 310 g (laboratoire) à 0,9 kg (bon marché) |
| Chauffe inégale autour de la tige | Simule une force latérale d'environ 26 g par degré d'amplitude. Le côté chaud doit rester à moins de 1,5 °C environ de la moyenne (0,28 °C pour un tube de 8 mm) |
| Fibre de référence en retard de 1 °C | 34 N d'erreur sur la voie axiale, voies latérales propres |
| Erreur de calibration de 5 % | 15 à 17 g d'erreur latérale |
| Réponse courbe de 5 % | Un modèle du second ordre ramène l'erreur latérale de 12 g à 3 g |

Tableaux complets : [docs/results_summary.md](docs/results_summary.md) (en anglais). Équations et hypothèses : [docs/model.md](docs/model.md) (en anglais).

## État d'avancement

| Élément | État |
|---|---|
| Simulation et décodage (`src/`, `scripts/`) | Écrits et testés contre leur propre modèle (13 tests, quatre scénarios). Résultats reproductibles : un nouveau calcul donne le même fichier |
| Calibration (`src/fbg_sim/calibration.py`, `scripts/fit_calibration.py`) | Écrite, testée sur données synthétiques seulement. Jamais utilisée sur des mesures |
| Modèle 3D du manchon (`hardware/`, `docs/plan_technique.md`) | Construit, géométrie contrôlée. Jamais imprimé ni essayé. Sans pièce déformable |
| Version OpenSCAD | Même géométrie, **non rendue** (OpenSCAD absent) |
| Câble, connecteur, protection de la fibre | Non conçus |
| Micrologiciel | Non écrit |
| Plan d'essai (`docs/test_plan.md`, `docs/calibration_procedure.md`) | Brouillon, non exécuté |
| Liste de pièces (`docs/bom_template.csv`) | Modèle vide, sans devis |
| Validation sur banc | Non faite |

## Démarrage

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_simulation.py
python scripts/make_results_summary.py
```

## Ce qui changerait les conclusions

Cinq hypothèses ne se règlent que sur un banc : la réponse thermique d'une fibre collée sur l'acier (30 pm/°C est une estimation sans mesure), le bruit réel de la lecture (1 pm n'a pas de source), la paroi, le bras de levier et la rigidité d'un vrai instrument, la part de déformation que la colle transmet réellement, et l'effet de l'orifice et de la main sur la poignée (le manchon reste hors de l'orifice : la force de pointe exige un modèle du point de pivot, qui n'existe pas ici).

Si vous pouvez faire l'un de ces essais, voyez [CONTRIBUTING.md](CONTRIBUTING.md). Un résultat négatif est aussi utile qu'un résultat positif.

## Brevets et sécurité

- Une famille de brevets existe sur des capteurs de force à nervures intégrés à la tige d'un instrument comme modules fabriqués séparément (par exemple US 9 952 107). **Ses revendications n'ont pas été lues.** Lisez-les avant de construire ou de redistribuer des dérivés. Ce n'est pas un avis juridique.
- Le dessin ne revendique ni stérilité ni usage médical. Rien n'est validé pour des patients.

## Comment ce dépôt a été produit

Le code, les figures et les documents ont été écrits avec l'aide d'une IA (Claude, d'Anthropic), puis exécutés et contrôlés avec les tests de `tests/`. Lisez le code avant de vous y fier. L'auteur est responsable de ce qui est publié ici.

## Licences

Logiciel : MIT (`LICENSE`). Matériel (`hardware/`) : licence CERN Open Hardware à venir, variante non choisie (voir `LICENSES/CERN-OHL-NOTE.md`).
