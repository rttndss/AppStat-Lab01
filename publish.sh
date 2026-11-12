#!/usr/bin/env bash
# Создаёт git-историю по этапам работы над лабой и (если передан адрес) отправляет её на GitHub.
#
#   bash publish.sh                                   # только локальная история
#   bash publish.sh https://github.com/ЛОГИН/РЕПО.git # история + отправка на GitHub
#
# Скрипт запускается один раз в распакованной папке. Сам он и папка _history в репозиторий не попадают.
set -euo pipefail
cd "$(dirname "$0")"

if [ -d .git ]; then
  echo "Здесь уже есть git-репозиторий. Скрипт нужен только для первой публикации."; exit 1
fi
if [ -z "$(git config user.name || true)" ] || [ -z "$(git config user.email || true)" ]; then
  echo "Сначала укажите имя и почту для коммитов (почта – та же, что в аккаунте GitHub):"
  echo '  git config --global user.name  "Имя Фамилия"'
  echo '  git config --global user.email "почта@example.com"'
  exit 1
fi

git init -q -b main
printf '_history/\npublish.sh\n.final/\n' >> .git/info/exclude   # вспомогательные файлы не коммитим

# Финальные версии временно убираем, чтобы восстанавливать их по шагам
mkdir -p .final
mv README.md Lab01_InfoChem_KTvD.ipynb ktvd_generator_marimo.py delaney-processed.csv winequality-red.csv .final/

commit () { git commit -q -m "$1"; echo "✓ $1"; }

# 1. Заготовка репозитория
cp _history/README_start.md README.md
git add README.md .gitignore requirements.txt
commit "Initial commit: описание работы, зависимости, .gitignore"

# 2. Датасет ИнфоХимии
mv .final/delaney-processed.csv .
git add delaney-processed.csv
commit "Выбран датасет ESOL (Delaney, 2004): растворимость органических соединений"

# 3. Спринты 1–2 ИнфоХимии (ноутбук из Colab)
cp _history/01_infochem_sprint1_2.ipynb Lab01_InfoChem_KTvD.ipynb
git add Lab01_InfoChem_KTvD.ipynb
commit "Спринты 1–2 (ИнфоХимия): EDA LogS, MW и TPSA, гипотезы, генератор для LogS (полярный метод и метод обратной функции)"

# 4. Блок КТвД – первая версия отдельным ноутбуком
mv .final/winequality-red.csv .
cp _history/02_ktvd_block.ipynb Lab01_KTvD.ipynb
git add winequality-red.csv Lab01_KTvD.ipynb
commit "Блок КТвД: датасет Wine Quality, pH и фиксированная кислотность – доказательство случайности, зависимость, EDA"

# 5. Объединение в один документ
mv .final/Lab01_InfoChem_KTvD.ipynb .
git rm -q Lab01_KTvD.ipynb
git add Lab01_InfoChem_KTvD.ipynb
commit "Объединение частей ИнфоХимии и КТвД: оглавление и нумерация, скрытый код, единый стиль графиков, исправлены числа и единицы, сравнение трёх методов генерации"

# 6. Интерактивный генератор
mv .final/ktvd_generator_marimo.py .
git add ktvd_generator_marimo.py
commit "Интерактивный генератор на marimo"

# 7. Итоговый README
mv .final/README.md .
git add README.md
commit "README: авторы, данные, чек-листы спринтов, среда работы"

rmdir .final
echo
git log --oneline
echo

if [ "${1:-}" != "" ]; then
  git remote add origin "$1"
  git push -u origin main
  echo; echo "Готово: история отправлена на $1"
else
  echo "Локальная история готова. Отправить на GitHub:"
  echo "  • GitHub Desktop: File → Add local repository → эта папка → Publish repository"
  echo "  • или в терминале: git remote add origin https://github.com/ЛОГИН/РЕПО.git && git push -u origin main"
fi
