#!/bin/sh
# Запуск кросс-системы GR1804 в DOSBox на Linux: эта папка монтируется как диск C:,
# RUS.COM включает кириллицу (cp866), затем стартует GR1804.
# Если нативного DOSBox нет, запускается DOSBox 0.74 из курса (dos.exe) через Wine
# с dosbox-lab4.conf (output=opengl, иначе окно под Wine перестает перерисовываться).
# В диалоге GR1804: любая клавиша, имя задачи LAB4, вариант 100, ПЗУ 256, «Считать файл задачи» Y.
cd "$(dirname "$0")" || exit 1
DIR="$(pwd)"
if command -v dosbox-x >/dev/null 2>&1; then
    exec dosbox-x -fastlaunch -nopromptfolder \
        -c "mount c \"$DIR\"" -c "c:" -c "rus" -c "gr1804"
elif command -v dosbox >/dev/null 2>&1; then
    exec dosbox -c "mount c \"$DIR\"" -c "c:" -c "rus" -c "gr1804"
else
    WINDIR="Z:$(printf '%s' "$DIR" | tr '/' '\\')"
    exec wine dos.exe -noconsole -conf dosbox-lab4.conf \
        -c "mount c \"$WINDIR\"" -c "c:" -c "rus" -c "gr1804"
fi
