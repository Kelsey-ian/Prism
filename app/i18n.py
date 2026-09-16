# -*- coding: utf-8 -*-
"""Prism i18n —— 多语言翻译系统。

使用紧凑的元组格式，每个键映射到 7 元素元组：
    (zh_CN, en, en_US, fr, ja, ru, es)

通过 ``t(key, **kwargs)`` 查找当前语言对应的文案，支持 ``{placeholder}`` 插值。
"""
from __future__ import annotations

import locale
import sys
from typing import List

from PySide6.QtCore import QObject, Signal


# ============================================================ 语言常量

SUPPORTED_LANGUAGES: List[str] = [
    "zh_CN", "zh_HK", "zh_TW", "en", "en_US", "fr", "ja", "ru", "es",
]
DEFAULT_LANGUAGE: str = "zh_CN"

# 元组顺序索引对应的语言代码
_LANGS: List[str] = ["zh_CN", "en", "en_US", "fr", "ja", "ru", "es"]

# 当前语言的英文回退索引
_EN_INDEX: int = 1

# 语言回退链：不在 _LANGS 中的代码映射到其回退语言
_FALLBACKS: dict = {
    "zh_HK": "zh_CN",
    "zh_TW": "zh_CN",
}


# ============================================================ 翻译表
# 顺序: (zh_CN, en, en_US, fr, ja, ru, es)

_T = {

    # ---------------------------------------------------- app.*
    "app.name": (
        "棱镜", "Prism", "Prism", "Prisme", "プリズム", "Призма", "Prisma",
    ),
    "app.subtitle": (
        "格式转换器", "Format Converter", "Format Converter",
        "Convertisseur de formats", "フォーマット変換ツール",
        "Конвертер форматов", "Convertidor de formatos",
    ),
    "app.version": (
        "1.0.0", "1.0.0", "1.0.0", "1.0.0", "1.0.0", "1.0.0", "1.0.0",
    ),

    # ---------------------------------------------------- common.*
    "common.ok": (
        "确定", "OK", "OK", "OK", "OK", "OK", "Aceptar",
    ),
    "common.cancel": (
        "取消", "Cancel", "Cancel", "Annuler", "キャンセル",
        "Отмена", "Cancelar",
    ),
    "common.close": (
        "关闭", "Close", "Close", "Fermer", "閉じる", "Закрыть", "Cerrar",
    ),
    "common.confirm": (
        "确认", "Confirm", "Confirm", "Confirmer", "確認",
        "Подтвердить", "Confirmar",
    ),
    "common.yes": (
        "是", "Yes", "Yes", "Oui", "はい", "Да", "Sí",
    ),
    "common.no": (
        "否", "No", "No", "Non", "いいえ", "Нет", "No",
    ),
    "common.retry": (
        "重试", "Retry", "Retry", "Réessayer", "再試行",
        "Повторить", "Reintentar",
    ),
    "common.apply": (
        "应用", "Apply", "Apply", "Appliquer", "適用",
        "Применить", "Aplicar",
    ),
    "common.save": (
        "保存", "Save", "Save", "Enregistrer", "保存",
        "Сохранить", "Guardar",
    ),
    "common.remove": (
        "移除", "Remove", "Remove", "Supprimer", "削除",
        "Удалить", "Quitar",
    ),
    "common.delete": (
        "删除", "Delete", "Delete", "Supprimer", "削除",
        "Удалить", "Eliminar",
    ),
    "common.add": (
        "添加", "Add", "Add", "Ajouter", "追加", "Добавить", "Añadir",
    ),
    "common.open": (
        "打开", "Open", "Open", "Ouvrir", "開く", "Открыть", "Abrir",
    ),
    "common.browse": (
        "浏览", "Browse", "Browse", "Parcourir", "参照",
        "Обзор", "Examinar",
    ),
    "common.later": (
        "稍后", "Later", "Later", "Plus tard", "後で",
        "Позже", "Más tarde",
    ),
    "common.download": (
        "立即下载", "Download now", "Download now",
        "Télécharger", "今すぐダウンロード",
        "Скачать", "Descargar",
    ),
    "common.unknown": (
        "未知", "Unknown", "Unknown", "Inconnu", "不明",
        "Неизвестно", "Desconocido",
    ),
    "common.not_detected": (
        "未检测到", "Not detected", "Not detected", "Non détecté",
        "検出されませんでした", "Не обнаружено", "No detectado",
    ),
    "common.not_installed": (
        "未安装", "Not installed", "Not installed", "Non installé",
        "未インストール", "Не установлено", "No instalado",
    ),
    "common.ready": (
        "准备就绪", "Ready", "Ready", "Prêt", "準備完了",
        "Готово", "Listo",
    ),
    "common.detecting": (
        "检测中…", "Detecting…", "Detecting…", "Détection…",
        "検出中…", "Обнаружение…", "Detectando…",
    ),

    # ---------------------------------------------------- nav.*
    "nav.convert": (
        "格式转换", "Convert", "Convert", "Convertir", "変換",
        "Конвертация", "Convertir",
    ),
    "nav.queue": (
        "任务队列", "Queue", "Queue", "File d'attente", "キュー",
        "Очередь", "Cola",
    ),
    "nav.settings": (
        "设置", "Settings", "Settings", "Paramètres", "設定",
        "Настройки", "Ajustes",
    ),
    "nav.help": (
        "帮助", "Help", "Help", "Aide", "ヘルプ", "Справка", "Ayuda",
    ),

    # ---------------------------------------------------- convert.*
    "convert.title": (
        "格式转换", "Format Conversion", "Format Conversion",
        "Conversion de formats", "フォーマット変換",
        "Конвертация форматов", "Conversión de formatos",
    ),
    "convert.subtitle": (
        "添加媒体文件，选择目标格式，一键批量转换",
        "Add media files, choose a target format, and convert in batch",
        "Add media files, choose a target format, and convert in batch",
        "Ajoutez des fichiers, choisissez un format cible et convertissez en lot",
        "メディアファイルを追加し、出力フォーマットを選んで一括変換",
        "Добавьте медиафайлы, выберите целевой формат и конвертируйте партиями",
        "Añada archivos multimedia, elija un formato de destino y convierta en lote",
    ),
    "convert.category.video": (
        "视频", "Video", "Video", "Vidéo", "動画",
        "Видео", "Vídeo",
    ),
    "convert.category.audio": (
        "音频", "Audio", "Audio", "Audio", "音声",
        "Аудио", "Audio",
    ),
    "convert.category.image": (
        "图片", "Image", "Image", "Image", "画像",
        "Изображение", "Imagen",
    ),
    "convert.current_mode": (
        "当前转换模式", "Current Conversion Mode", "Current Mode",
        "Mode de conversion actuel", "現在の変換モード",
        "Текущий режим конвертации", "Modo de conversión actual",
    ),

    # 文件对话框过滤器
    "convert.filter.video": (
        "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.mpg *.mpeg *.3gp *.ts *.m2ts *.mts *.vob *.ogv *.rmvb *.m4v);;所有文件 (*.*)",
        "Video files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.mpg *.mpeg *.3gp *.ts *.m2ts *.mts *.vob *.ogv *.rmvb *.m4v);;All files (*.*)",
        "Video files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.mpg *.mpeg *.3gp *.ts *.m2ts *.mts *.vob *.ogv *.rmvb *.m4v);;All files (*.*)",
        "Fichiers vidéo (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.mpg *.mpeg *.3gp *.ts *.m2ts *.mts *.vob *.ogv *.rmvb *.m4v);;Tous les fichiers (*.*)",
        "動画ファイル (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.mpg *.mpeg *.3gp *.ts *.m2ts *.mts *.vob *.ogv *.rmvb *.m4v);;すべてのファイル (*.*)",
        "Видеофайлы (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.mpg *.mpeg *.3gp *.ts *.m2ts *.mts *.vob *.ogv *.rmvb *.m4v);;Все файлы (*.*)",
        "Archivos de vídeo (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.mpg *.mpeg *.3gp *.ts *.m2ts *.mts *.vob *.ogv *.rmvb *.m4v);;Todos los archivos (*.*)",
    ),
    "convert.filter.audio": (
        "音频文件 (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.amr *.ape *.m4b *.ac3);;所有文件 (*.*)",
        "Audio files (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.amr *.ape *.m4b *.ac3);;All files (*.*)",
        "Audio files (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.amr *.ape *.m4b *.ac3);;All files (*.*)",
        "Fichiers audio (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.amr *.ape *.m4b *.ac3);;Tous les fichiers (*.*)",
        "音声ファイル (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.amr *.ape *.m4b *.ac3);;すべてのファイル (*.*)",
        "Аудиофайлы (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.amr *.ape *.m4b *.ac3);;Все файлы (*.*)",
        "Archivos de audio (*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.amr *.ape *.m4b *.ac3);;Todos los archivos (*.*)",
    ),
    "convert.filter.image": (
        "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.ico *.heic *.heif *.avif *.jfif);;所有文件 (*.*)",
        "Image files (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.ico *.heic *.heif *.avif *.jfif);;All files (*.*)",
        "Image files (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.ico *.heic *.heif *.avif *.jfif);;All files (*.*)",
        "Fichiers image (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.ico *.heic *.heif *.avif *.jfif);;Tous les fichiers (*.*)",
        "画像ファイル (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.ico *.heic *.heif *.avif *.jfif);;すべてのファイル (*.*)",
        "Файлы изображений (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.ico *.heic *.heif *.avif *.jfif);;Все файлы (*.*)",
        "Archivos de imagen (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.ico *.heic *.heif *.avif *.jfif);;Todos los archivos (*.*)",
    ),
    "convert.filter.all_files": (
        "所有文件 (*.*)", "All files (*.*)", "All files (*.*)",
        "Tous les fichiers (*.*)", "すべてのファイル (*.*)",
        "Все файлы (*.*)", "Todos los archivos (*.*)",
    ),

    # 冲突策略
    "convert.conflict.rename": (
        "自动重命名（推荐）", "Auto rename (recommended)",
        "Auto rename (recommended)",
        "Renommer automatiquement (recommandé)",
        "自動リネーム（推奨）",
        "Авто-переименование (рекомендуется)",
        "Renombrar automáticamente (recomendado)",
    ),
    "convert.conflict.overwrite": (
        "直接覆盖", "Overwrite", "Overwrite",
        "Écraser", "上書き", "Перезаписать", "Sobrescribir",
    ),
    "convert.conflict.skip": (
        "跳过已存在的文件", "Skip existing files",
        "Skip existing files",
        "Ignorer les fichiers existants",
        "既存ファイルをスキップ",
        "Пропустить существующие файлы",
        "Omitir archivos existentes",
    ),

    # 状态单元格默认
    "convert.status_cell.default": (
        "待转换", "Pending", "Pending", "En attente", "変換待ち",
        "Ожидает", "Pendiente",
    ),

    # 文件列表
    "convert.file_list.title": (
        "文件列表", "File List", "File List",
        "Liste de fichiers", "ファイルリスト",
        "Список файлов", "Lista de archivos",
    ),
    "convert.file_list.count": (
        "{count} 个文件", "{count} files", "{count} files",
        "{count} fichiers", "{count} ファイル",
        "{count} файлов", "{count} archivos",
    ),
    "convert.file_list.count_zero": (
        "0 个文件", "0 files", "0 files",
        "0 fichier", "0 ファイル", "0 файлов", "0 archivos",
    ),
    "convert.file_list.add_files": (
        "添加文件", "Add Files", "Add Files",
        "Ajouter des fichiers", "ファイルを追加",
        "Добавить файлы", "Añadir archivos",
    ),
    "convert.file_list.add_folder": (
        "添加文件夹", "Add Folder", "Add Folder",
        "Ajouter un dossier", "フォルダーを追加",
        "Добавить папку", "Añadir carpeta",
    ),
    "convert.file_list.clear": (
        "清空", "Clear", "Clear",
        "Vider", "クリア", "Очистить", "Limpiar",
    ),

    # 表格列标题
    "convert.column.filename": (
        "文件名", "File Name", "File Name",
        "Nom du fichier", "ファイル名",
        "Имя файла", "Nombre de archivo",
    ),
    "convert.column.source_format": (
        "源格式", "Source Format", "Source Format",
        "Format source", "元フォーマット",
        "Исходный формат", "Formato de origen",
    ),
    "convert.column.size": (
        "大小", "Size", "Size",
        "Taille", "サイズ", "Размер", "Tamaño",
    ),
    "convert.column.media_info": (
        "媒体信息", "Media Info", "Media Info",
        "Infos média", "メディア情報",
        "Информация о медиа", "Información multimedia",
    ),
    "convert.column.status": (
        "状态", "Status", "Status",
        "Statut", "ステータス", "Статус", "Estado",
    ),
    "convert.column.action": (
        "操作", "Action", "Action",
        "Action", "操作", "Действие", "Acción",
    ),
    "convert.column.target_format": (
        "目标格式", "Target Format", "Target Format",
        "Format cible", "出力フォーマット",
        "Целевой формат", "Formato de destino",
    ),
    "convert.column.output_dir": (
        "输出目录", "Output Directory", "Output Directory",
        "Dossier de sortie", "出力ディレクトリ",
        "Папка вывода", "Directorio de salida",
    ),
    "convert.column.status_progress": (
        "状态 / 进度", "Status / Progress", "Status / Progress",
        "Statut / Progression", "ステータス / 進捗",
        "Статус / Прогресс", "Estado / Progreso",
    ),

    # 输出设置
    "convert.output.title": (
        "输出设置", "Output Settings", "Output Settings",
        "Paramètres de sortie", "出力設定",
        "Настройки вывода", "Ajustes de salida",
    ),
    "convert.output.format": (
        "输出格式", "Output Format", "Output Format",
        "Format de sortie", "出力フォーマット",
        "Формат вывода", "Formato de salida",
    ),
    "convert.output.preset": (
        "质量预设", "Quality Preset", "Quality Preset",
        "Préréglage qualité", "品質プリセット",
        "Пресет качества", "Preset de calidad",
    ),
    "convert.output.resolution": (
        "视频分辨率", "Video Resolution", "Video Resolution",
        "Résolution vidéo", "動画解像度",
        "Разрешение видео", "Resolución de vídeo",
    ),
    "convert.output.fps": (
        "视频帧率", "Frame Rate", "Frame Rate",
        "Fréquence d'images", "フレームレート",
        "Частота кадров", "Tasa de fotogramas",
    ),
    "convert.output.destination": (
        "输出到", "Output to", "Output to",
        "Sortie vers", "出力先", "Вывод в", "Salida a",
    ),
    "convert.output.source_dir": (
        "源文件所在文件夹", "Source file folder", "Source file folder",
        "Dossier du fichier source", "元ファイルのフォルダー",
        "Папка исходного файла", "Carpeta del archivo de origen",
    ),
    "convert.output.custom_dir": (
        "自定义文件夹", "Custom folder", "Custom folder",
        "Dossier personnalisé", "カスタムフォルダー",
        "Своя папка", "Carpeta personalizada",
    ),
    "convert.output.dir_placeholder": (
        "点击右侧按钮选择输出目录",
        "Click the button on the right to select an output directory",
        "Click the button on the right to select an output directory",
        "Cliquez sur le bouton à droite pour choisir un dossier de sortie",
        "右のボタンをクリックして出力ディレクトリを選択",
        "Нажмите кнопку справа, чтобы выбрать папку вывода",
        "Haga clic en el botón de la derecha para seleccionar un directorio de salida",
    ),
    "convert.output.conflict": (
        "同名文件", "Name conflicts", "Name conflicts",
        "Fichiers en conflit", "同名ファイル",
        "Совпадающие имена", "Conflictos de nombre",
    ),
    "convert.output.res_width": (
        "宽", "Width", "Width",
        "Largeur", "幅", "Ширина", "Ancho",
    ),
    "convert.output.res_height": (
        "高", "Height", "Height",
        "Hauteur", "高さ", "Высота", "Alto",
    ),

    # 底部操作行
    "convert.summary.ready": (
        "准备就绪", "Ready", "Ready",
        "Prêt", "準備完了", "Готово", "Listo",
    ),
    "convert.summary.total": (
        "共 {count} 个文件", "{count} files in total", "{count} files in total",
        "{count} fichiers au total", "合計 {count} ファイル",
        "Всего {count} файлов", "{count} archivos en total",
    ),
    "convert.summary.enqueued": (
        "共 {total} 个文件，{enqueued} 个已在队列",
        "{total} files in total, {enqueued} already queued",
        "{total} files in total, {enqueued} already queued",
        "{total} fichiers au total, {enqueued} déjà en file",
        "合計 {total} ファイル、{enqueued} 件がキューに登録済み",
        "Всего {total} файлов, {enqueued} уже в очереди",
        "{total} archivos en total, {enqueued} ya en cola",
    ),
    "convert.start": (
        "开始转换", "Start Conversion", "Start Conversion",
        "Démarrer la conversion", "変換を開始",
        "Начать конвертацию", "Iniciar conversión",
    ),

    # 文件选择对话框
    "convert.dialog.choose_folder": (
        "选择包含媒体文件的文件夹",
        "Select a folder containing media files",
        "Select a folder containing media files",
        "Sélectionner un dossier contenant des fichiers multimédia",
        "メディアファイルを含むフォルダーを選択",
        "Выберите папку с медиафайлами",
        "Seleccione una carpeta que contenga archivos multimedia",
    ),
    "convert.dialog.choose_output_folder": (
        "选择输出文件夹", "Select output folder",
        "Select output folder",
        "Sélectionner le dossier de sortie",
        "出力フォルダーを選択",
        "Выберите папку вывода",
        "Seleccionar carpeta de salida",
    ),
    "convert.dialog.choose_files": (
        "选择要转换的文件", "Select files to convert",
        "Select files to convert",
        "Sélectionner les fichiers à convertir",
        "変換するファイルを選択",
        "Выберите файлы для конвертации",
        "Seleccione los archivos a convertir",
    ),

    # ---------------------------------------------------- drop card
    "drop.title": (
        "拖放文件到此处，或点击选择文件",
        "Drop files here, or click to select",
        "Drop files here, or click to select",
        "Déposez les fichiers ici, ou cliquez pour sélectionner",
        "ファイルをドラッグ＆ドロップ、またはクリックして選択",
        "Перетащите файлы сюда или нажмите, чтобы выбрать",
        "Suelta archivos aquí o haz clic para seleccionar",
    ),
    "drop.hint": (
        "支持批量添加 · 支持拖入文件夹自动扫描 · 音频 / 视频 / 图片",
        "Batch add · Auto-scan folders · Audio / Video / Image",
        "Batch add · Auto-scan folders · Audio / Video / Image",
        "Ajout par lot · Analyse auto des dossiers · Audio / Vidéo / Image",
        "一括追加・フォルダ自動スキャン・音声 / 動画 / 画像",
        "Пакетное добавление · Автоскан папок · Аудио / Видео / Изображение",
        "Añadir por lotes · Auto-escanear carpetas · Audio / Vídeo / Imagen",
    ),

    # 操作工具提示
    "convert.tip.open_output_dir": (
        "打开输出所在文件夹", "Open output folder",
        "Open output folder",
        "Ouvrir le dossier de sortie",
        "出力フォルダーを開く",
        "Открыть папку вывода",
        "Abrir carpeta de salida",
    ),
    "convert.tip.remove": (
        "移除", "Remove", "Remove",
        "Supprimer", "削除", "Удалить", "Quitar",
    ),

    # InfoBar 消息
    "convert.info.no_media.title": (
        "未发现可转换的媒体文件", "No convertible media files found",
        "No convertible media files found",
        "Aucun fichier média convertible trouvé",
        "変換可能なメディアファイルが見つかりません",
        "Конвертируемые медиафайлы не найдены",
        "No se encontraron archivos multimedia convertibles",
    ),
    "convert.info.no_media.content": (
        "不支持的项目：{items}",
        "Unsupported items: {items}",
        "Unsupported items: {items}",
        "Éléments non pris en charge : {items}",
        "対応していない項目: {items}",
        "Неподдерживаемые элементы: {items}",
        "Elementos no admitidos: {items}",
    ),
    "convert.info.added.title": (
        "添加成功", "Files added", "Files added",
        "Fichiers ajoutés", "追加完了",
        "Файлы добавлены", "Archivos añadidos",
    ),
    "convert.info.added.content": (
        "已添加 {count} 个文件",
        "Added {count} files",
        "Added {count} files",
        "{count} fichiers ajoutés",
        "{count} ファイルを追加しました",
        "Добавлено {count} файлов",
        "{count} archivos añadidos",
    ),
    "convert.info.added.other": (
        "已添加 {count} 个文件，其中 {other} 个在其他分类页",
        "Added {count} files, {other} of which are in other categories",
        "Added {count} files, {other} of which are in other categories",
        "{count} fichiers ajoutés, dont {other} dans d'autres catégories",
        "{count} ファイルを追加しました（うち {other} 件は別カテゴリページ）",
        "Добавлено {count} файлов, {other} в других категориях",
        "Añadidos {count} archivos, {other} en otras categorías",
    ),
    "convert.info.other_category.title": (
        "文件已加入其他分类", "Files added to other categories",
        "Files added to other categories",
        "Fichiers ajoutés à d'autres catégories",
        "ファイルは別のカテゴリに追加されました",
        "Файлы добавлены в другие категории",
        "Archivos añadidos a otras categorías",
    ),
    "convert.info.other_category.content": (
        "{count} 个文件不属于“{category}”，请切换到对应分类页查看",
        "{count} files do not belong to \"{category}\". Switch to the matching category to view them.",
        "{count} files do not belong to \"{category}\". Switch to the matching category to view them.",
        "{count} fichiers n'appartiennent pas à « {category} ». Basculez vers la catégorie correspondante pour les voir.",
        "{count} 件のファイルは「{category}」に属しません。該当カテゴリページに切り替えてご確認ください。",
        "{count} файлов не относятся к «{category}». Перейдите в нужную категорию для просмотра.",
        "{count} archivos no pertenecen a «{category}». Cambie a la categoría correspondiente para verlos.",
    ),
    "convert.info.unsupported.title": (
        "存在不支持的文件", "Unsupported files detected",
        "Unsupported files detected",
        "Fichiers non pris en charge détectés",
        "対応していないファイルがあります",
        "Обнаружены неподдерживаемые файлы",
        "Se detectaron archivos no admitidos",
    ),
    "convert.info.unsupported.content": (
        "{count} 个项目被跳过：{items}",
        "{count} items skipped: {items}",
        "{count} items skipped: {items}",
        "{count} éléments ignorés : {items}",
        "{count} 件の項目をスキップしました: {items}",
        "Пропущено {count} элементов: {items}",
        "{count} elementos omitidos: {items}",
    ),
    "convert.info.cannot_clear.title": (
        "无法清空", "Cannot clear", "Cannot clear",
        "Impossible de vider", "クリアできません",
        "Нельзя очистить", "No se puede limpiar",
    ),
    "convert.info.cannot_clear.content": (
        "已加入队列的文件请在任务队列页移除",
        "Please remove queued files from the Queue page",
        "Please remove queued files from the Queue page",
        "Veuillez retirer les fichiers en file d'attente depuis la page File d'attente",
        "キューに登録済みのファイルはタスクキュー画面で削除してください",
        "Удалите файлы в очереди на странице «Очередь»",
        "Elimine los archivos en cola desde la página Cola",
    ),
    "convert.info.task_running.title": (
        "任务进行中", "Task in progress", "Task in progress",
        "Tâche en cours", "タスク実行中",
        "Задача выполняется", "Tarea en curso",
    ),
    "convert.info.task_running.content": (
        "请先在任务队列页取消该任务",
        "Please cancel this task on the Queue page first",
        "Please cancel this task on the Queue page first",
        "Veuillez d'abord annuler cette tâche sur la page File d'attente",
        "先にタスクキュー画面でこのタスクをキャンセルしてください",
        "Сначала отмените задачу на странице «Очередь»",
        "Primero cancele esta tarea en la página Cola",
    ),
    "convert.info.no_ffmpeg.title": (
        "尚未安装 FFmpeg", "FFmpeg not installed",
        "FFmpeg not installed",
        "FFmpeg n'est pas installé",
        "FFmpegが未インストールです",
        "FFmpeg не установлен",
        "FFmpeg no está instalado",
    ),
    "convert.info.no_ffmpeg.content": (
        "请前往“设置”页面下载内置 FFmpeg 后再开始转换",
        "Please go to Settings to download the bundled FFmpeg before converting",
        "Please go to Settings to download the bundled FFmpeg before converting",
        "Veuillez télécharger FFmpeg depuis les Paramètres avant de convertir",
        "「設定」ページで内蔵 FFmpegをダウンロードしてから変換を開始してください",
        "Скачайте встроенный FFmpeg на странице «Настройки» перед конвертацией",
        "Descargue FFmpeg integrado en Ajustes antes de convertir",
    ),
    "convert.info.no_format.title": (
        "请选择输出格式", "Please select an output format",
        "Please select an output format",
        "Veuillez sélectionner un format de sortie",
        "出力フォーマットを選択してください",
        "Выберите формат вывода",
        "Seleccione un formato de salida",
    ),
    "convert.info.no_new_files.title": (
        "没有可转换的新文件", "No new files to convert",
        "No new files to convert",
        "Aucun nouveau fichier à convertir",
        "変換できる新しいファイルがありません",
        "Нет новых файлов для конвертации",
        "No hay archivos nuevos para convertir",
    ),
    "convert.info.no_new_files.content": (
        "文件已全部加入队列",
        "All files are already queued",
        "All files are already queued",
        "Tous les fichiers sont déjà en file",
        "すべてのファイルはすでにキューに登録されています",
        "Все файлы уже в очереди",
        "Todos los archivos ya están en cola",
    ),
    "convert.info.invalid_dir.title": (
        "输出目录无效", "Invalid output directory",
        "Invalid output directory",
        "Dossier de sortie invalide",
        "出力ディレクトリが無効です",
        "Недопустимая папка вывода",
        "Directorio de salida no válido",
    ),
    "convert.info.invalid_dir.content": (
        "请选择一个存在的自定义文件夹",
        "Please select an existing custom folder",
        "Please select an existing custom folder",
        "Veuillez sélectionner un dossier personnalisé existant",
        "存在するカスタムフォルダーを選択してください",
        "Выберите существующую папку",
        "Seleccione una carpeta personalizada existente",
    ),
    "convert.info.invalid_resolution.title": (
        "分辨率无效", "Invalid Resolution", "Invalid Resolution",
        "Résolution invalide", "解像度が無効",
        "Недопустимое разрешение", "Resolución no válida",
    ),
    "convert.info.invalid_resolution.content": (
        "请输入有效的宽度和高度数值",
        "Please enter valid width and height values",
        "Please enter valid width and height values",
        "Veuillez saisir des valeurs de largeur et de hauteur valides",
        "有効な幅と高さの数値を入力してください",
        "Введите допустимые значения ширины и высоты",
        "Introduzca valores válidos de ancho y alto",
    ),
    "convert.info.invalid_resolution.range": (
        "分辨率范围应为 16–8192 像素",
        "Resolution range should be 16–8192 pixels",
        "Resolution range should be 16–8192 pixels",
        "La plage de résolution doit être de 16 à 8192 pixels",
        "解像度範囲は 16～8192 ピクセルにしてください",
        "Диапазон разрешения: 16–8192 пикселей",
        "El rango de resolución debe ser de 16 a 8192 píxeles",
    ),
    "convert.info.enqueued.title": (
        "已加入转换队列", "Added to conversion queue",
        "Added to conversion queue",
        "Ajouté à la file de conversion",
        "変換キューに追加しました",
        "Добавлено в очередь конвертации",
        "Añadido a la cola de conversión",
    ),
    "convert.info.enqueued.content": (
        "{count} 个任务已开始，可在“任务队列”页查看进度",
        "{count} tasks started. View progress on the Queue page.",
        "{count} tasks started. View progress on the Queue page.",
        "{count} tâches démarrées. Suivez la progression sur la page File d'attente.",
        "{count} 件のタスクを開始しました。タスクキュー画面で進捗を確認できます。",
        "{count} задач запущено. Прогресс — на странице «Очередь».",
        "{count} tareas iniciadas. Vea el progreso en la página Cola.",
    ),
    "convert.info.auto_switched.title": (
        "已自动切换转换模式",
        "Conversion mode auto-switched",
        "Conversion mode auto-switched",
        "Mode de conversion automatiquement basculé",
        "変換モードを自動的に切り替えました",
        "Режим конвертации автоматически переключен",
        "Modo de conversión cambiado automáticamente",
    ),
    "convert.info.auto_switched.content": (
        "已切换至「{category}」转换模式",
        "Switched to «{category}» conversion mode",
        "Switched to «{category}» conversion mode",
        "Basculé vers le mode « {category} »",
        "「{category}」変換モードに切り替えました",
        "Переключено в режим «{category}»",
        "Cambiado al modo de conversión «{category}»",
    ),

    # ---------------------------------------------------- queue.*
    "queue.title": (
        "任务队列", "Task Queue", "Task Queue",
        "File d'attente", "タスクキュー",
        "Очередь задач", "Cola de tareas",
    ),
    "queue.subtitle": (
        "管理所有转换任务，支持并发执行与失败重试",
        "Manage all conversion tasks with concurrent execution and failure retry",
        "Manage all conversion tasks with concurrent execution and failure retry",
        "Gérez toutes les tâches de conversion avec exécution simultanée et réessai en cas d'échec",
        "すべての変換タスクを管理。並列実行と失敗時の再試行をサポート",
        "Управляйте всеми задачами конвертации с параллельным выполнением и повтором при сбое",
        "Administre todas las tareas de conversión con ejecución simultánea y reintento de fallos",
    ),
    "queue.btn.pause": (
        "暂停队列", "Pause Queue", "Pause Queue",
        "Mettre en pause", "キューを一時停止",
        "Приостановить очередь", "Pausar cola",
    ),
    "queue.btn.resume": (
        "继续队列", "Resume Queue", "Resume Queue",
        "Reprendre", "キューを再開",
        "Возобновить очередь", "Reanudar cola",
    ),
    "queue.btn.cancel_all": (
        "全部取消", "Cancel All", "Cancel All",
        "Tout annuler", "すべてキャンセル",
        "Отменить все", "Cancelar todo",
    ),
    "queue.btn.retry_failed": (
        "重试失败", "Retry Failed", "Retry Failed",
        "Réessayer les échecs", "失敗を再試行",
        "Повторить сбойные", "Reintentar fallidos",
    ),
    "queue.btn_clear_finished": (
        "清空已完成", "Clear Finished", "Clear Finished",
        "Vider les terminées", "完了をクリア",
        "Очистить завершённые", "Limpiar finalizados",
    ),
    "queue.concurrency": (
        "同时转换", "Concurrent", "Concurrent",
        "Simultané", "同時変換",
        "Параллельно", "Simultáneo",
    ),

    # 空状态
    "queue.empty.hint": (
        "队列中还没有任务", "No tasks in the queue",
        "No tasks in the queue",
        "Aucune tâche dans la file",
        "キューにタスクがありません",
        "В очереди нет задач",
        "No hay tareas en la cola",
    ),
    "queue.empty.desc": (
        "回到“格式转换”页面，拖入文件即可开始批量转换",
        "Go to the Convert page and drop files to start batch conversion",
        "Go to the Convert page and drop files to start batch conversion",
        "Retournez à la page Convertir et déposez des fichiers pour démarrer la conversion par lot",
        "「フォーマット変換」ページに戻り、ファイルをドロップして一括変換を開始",
        "Перейдите на «Конвертацию» и перетащите файлы для пакетной конвертации",
        "Vaya a la página Convertir y suelte archivos para iniciar la conversión por lote",
    ),
    "queue.empty.go_add": (
        "去添加文件", "Add Files", "Add Files",
        "Ajouter des fichiers", "ファイルを追加",
        "Добавить файлы", "Añadir archivos",
    ),

    # 操作工具提示
    "queue.tip.cancel_task": (
        "取消任务", "Cancel task", "Cancel task",
        "Annuler la tâche", "タスクをキャンセル",
        "Отменить задачу", "Cancelar tarea",
    ),
    "queue.tip.retry": (
        "重新转换", "Convert again", "Convert again",
        "Convertir à nouveau", "再変換",
        "Конвертировать снова", "Convertir de nuevo",
    ),
    "queue.tip.open_output_dir": (
        "打开输出所在文件夹", "Open output folder",
        "Open output folder",
        "Ouvrir le dossier de sortie",
        "出力フォルダーを開く",
        "Открыть папку вывода",
        "Abrir carpeta de salida",
    ),
    "queue.tip.remove_task": (
        "移除任务", "Remove task", "Remove task",
        "Supprimer la tâche", "タスクを削除",
        "Удалить задачу", "Quitar tarea",
    ),

    # 汇总
    "queue.summary.total": (
        "共 {count} 个", "{count} total", "{count} total",
        "{count} au total", "合計 {count}",
        "Всего {count}", "{count} en total",
    ),
    "queue.summary.running": (
        "转换中 {count}", "{count} running", "{count} running",
        "{count} en cours", "変換中 {count}",
        "{count} выполняется", "{count} en curso",
    ),
    "queue.summary.waiting": (
        "等待 {count}", "{count} waiting", "{count} waiting",
        "{count} en attente", "待機 {count}",
        "{count} ожидает", "{count} en espera",
    ),
    "queue.summary.done": (
        "完成 {count}", "{count} done", "{count} done",
        "{count} terminées", "完了 {count}",
        "{count} завершено", "{count} completados",
    ),
    "queue.summary.failed": (
        "失败 {count}", "{count} failed", "{count} failed",
        "{count} échouées", "失敗 {count}",
        "{count} сбоев", "{count} fallidos",
    ),
    "queue.summary.separator": (
        "　·　", " · ", " · ", " · ", " · ", " · ", " · ",
    ),

    # ---------------------------------------------------- settings.ffmpeg.*
    "settings.subtitle": (
        "管理 FFmpeg 引擎、硬件加速、界面外观与更新选项",
        "Manage FFmpeg engine, hardware acceleration, appearance and update options",
        "Manage FFmpeg engine, hardware acceleration, appearance and update options",
        "Gérer le moteur FFmpeg, l'accélération matérielle, l'apparence et les mises à jour",
        "FFmpegエンジン、ハードウェアアクセラレーション、外観、更新オプションの管理",
        "Управление движком FFmpeg, аппаратным ускорением, внешним видом и обновлениями",
        "Gestionar motor FFmpeg, aceleración por hardware, apariencia y actualizaciones",
    ),
    "settings.ffmpeg.title": (
        "FFmpeg 转换引擎", "FFmpeg Engine", "FFmpeg Engine",
        "Moteur FFmpeg", "FFmpeg 変換エンジン",
        "Движок FFmpeg", "Motor FFmpeg",
    ),
    "settings.ffmpeg.status_detecting": (
        "检测中…", "Detecting…", "Detecting…",
        "Détection…", "検出中…", "Обнаружение…", "Detectando…",
    ),
    "settings.ffmpeg.version_label": (
        "当前版本：{version}",
        "Current version: {version}",
        "Current version: {version}",
        "Version actuelle : {version}",
        "現在のバージョン: {version}",
        "Текущая версия: {version}",
        "Versión actual: {version}",
    ),
    "settings.ffmpeg.version_none": (
        "当前版本：—", "Current version: —", "Current version: —",
        "Version actuelle : —", "現在のバージョン: —",
        "Текущая версия: —", "Versión actual: —",
    ),
    "settings.ffmpeg.version_not_found": (
        "当前版本：未检测到 FFmpeg",
        "Current version: FFmpeg not detected",
        "Current version: FFmpeg not detected",
        "Version actuelle : FFmpeg non détecté",
        "現在のバージョン: FFmpeg未検出",
        "Текущая версия: FFmpeg не обнаружен",
        "Versión actual: FFmpeg no detectado",
    ),
    "settings.ffmpeg.version_with_source": (
        "当前版本：FFmpeg {version}（{source}）",
        "Current version: FFmpeg {version} ({source})",
        "Current version: FFmpeg {version} ({source})",
        "Version actuelle : FFmpeg {version} ({source})",
        "現在のバージョン: FFmpeg {version}（{source}）",
        "Текущая версия: FFmpeg {version} ({source})",
        "Versión actual: FFmpeg {version} ({source})",
    ),
    "settings.ffmpeg.path_label": (
        "路径：{path}", "Path: {path}", "Path: {path}",
        "Chemin : {path}", "パス: {path}",
        "Путь: {path}", "Ruta: {path}",
    ),
    "settings.ffmpeg.path_none": (
        "路径：—", "Path: —", "Path: —",
        "Chemin : —", "パス: —", "Путь: —", "Ruta: —",
    ),
    "settings.ffmpeg.path_hint": (
        "路径：—（点击下方按钮自动下载内置版本）",
        "Path: — (click the button below to download the bundled version)",
        "Path: — (click the button below to download the bundled version)",
        "Chemin : — (cliquez sur le bouton ci-dessous pour télécharger la version intégrée)",
        "パス: —（下のボタンをクリックして内蔵版をダウンロード）",
        "Путь: — (нажмите кнопку ниже, чтобы скачать встроенную версию)",
        "Ruta: — (haga clic en el botón de abajo para descargar la versión integrada)",
    ),
    "settings.ffmpeg.btn_detect": (
        "重新检测", "Re-detect", "Re-detect",
        "Redétecter", "再検出",
        "Перепроверить", "Volver a detectar",
    ),
    "settings.ffmpeg.btn_manual": (
        "手动选择", "Manual select", "Manual select",
        "Sélection manuelle", "手動選択",
        "Выбрать вручную", "Selección manual",
    ),
    "settings.ffmpeg.btn_about": (
        "关于 FFmpeg", "About FFmpeg", "About FFmpeg",
        "À propos de FFmpeg", "FFmpegについて",
        "О FFmpeg", "Acerca de FFmpeg",
    ),
    "settings.ffmpeg.btn_check_update": (
        "检查更新", "Check for updates", "Check for updates",
        "Vérifier les mises à jour", "更新を確認",
        "Проверить обновления", "Buscar actualizaciones",
    ),
    "settings.ffmpeg.btn_download": (
        "下载内置 FFmpeg", "Download bundled FFmpeg",
        "Download bundled FFmpeg",
        "Télécharger FFmpeg intégré",
        "内蔵 FFmpegをダウンロード",
        "Скачать встроенный FFmpeg",
        "Descargar FFmpeg integrado",
    ),
    "settings.ffmpeg.btn_download_version": (
        "下载新版本 {version}",
        "Download version {version}",
        "Download version {version}",
        "Télécharger la version {version}",
        "新バージョン {version} をダウンロード",
        "Скачать версию {version}",
        "Descargar versión {version}",
    ),
    "settings.ffmpeg.staged_hint": (
        "已下载更新包 {version}，将在退出程序后自动安装",
        "Update package {version} downloaded; will install on exit",
        "Update package {version} downloaded; will install on exit",
        "Mise à jour {version} téléchargée, installation à la fermeture",
        "更新パッケージ {version} をダウンロード済み。終了時に自動インストールします",
        "Пакет обновления {version} скачан, будет установлен при выходе",
        "Paquete de actualización {version} descargado; se instalará al salir",
    ),
    "settings.ffmpeg.pill_ready": (
        "● 已就绪", "● Ready", "● Ready",
        "● Prêt", "● 準備完了", "● Готово", "● Listo",
    ),
    "settings.ffmpeg.pill_not_installed": (
        "● 未安装", "● Not installed", "● Not installed",
        "● Non installé", "● 未インストール",
        "● Не установлено", "● No instalado",
    ),
    "settings.ffmpeg.info_detect_success.title": (
        "检测成功", "Detection successful", "Detection successful",
        "Détection réussie", "検出成功",
        "Обнаружение успешно", "Detección correcta",
    ),
    "settings.ffmpeg.info_not_found.title": (
        "未检测到 FFmpeg", "FFmpeg not detected",
        "FFmpeg not detected",
        "FFmpeg non détecté", "FFmpeg未検出",
        "FFmpeg не обнаружен", "FFmpeg no detectado",
    ),
    "settings.ffmpeg.info_not_found.content": (
        "可自动下载安装官方构建",
        "Can automatically download and install the official build",
        "Can automatically download and install the official build",
        "Téléchargement automatique de la version officielle possible",
        "公式ビルドを自動でダウンロード・インストールできます",
        "Можно автоматически скачать и установить официальную сборку",
        "Puede descargar e instalar automáticamente la compilación oficial",
    ),
    "settings.ffmpeg.caption_connecting": (
        "正在连接更新服务器比对版本…",
        "Connecting to the update server to compare versions…",
        "Connecting to the update server to compare versions…",
        "Connexion au serveur de mise à jour pour comparer les versions…",
        "更新サーバーに接続してバージョンを比較しています…",
        "Подключение к серверу обновлений для сравнения версий…",
        "Conectando al servidor de actualizaciones para comparar versiones…",
    ),
    "settings.ffmpeg.caption_preparing_download": (
        "准备下载…", "Preparing download…", "Preparing download…",
        "Préparation du téléchargement…",
        "ダウンロードを準備しています…",
        "Подготовка загрузки…", "Preparando descarga…",
    ),
    "settings.ffmpeg.caption_preparing_staging": (
        "准备下载更新包…", "Preparing to download update package…",
        "Preparing to download update package…",
        "Préparation du téléchargement de la mise à jour…",
        "更新パッケージのダウンロードを準備しています…",
        "Подготовка к загрузке пакета обновления…",
        "Preparando descarga del paquete de actualización…",
    ),
    "settings.ffmpeg.dialog_new_version.title": (
        "发现 FFmpeg 新版本", "New FFmpeg version available",
        "New FFmpeg version available",
        "Nouvelle version de FFmpeg disponible",
        "FFmpegの新バージョンがあります",
        "Доступна новая версия FFmpeg",
        "Nueva versión de FFmpeg disponible",
    ),
    "settings.ffmpeg.dialog_new_version.content": (
        "最新版本：{version}\n\n是否立即下载更新包？\n"
        "更新包仅在后台下载暂存，不会替换正在使用的引擎，"
        "因此不会打断任何转换任务；将在你正常退出程序后自动安装。",
        "Latest version: {version}\n\nDownload the update package now?\n"
        "The package is staged in the background without replacing the running engine, "
        "so no conversion is interrupted. It installs automatically after you exit.",
        "Latest version: {version}\n\nDownload the update package now?\n"
        "The package is staged in the background without replacing the running engine, "
        "so no conversion is interrupted. It installs automatically after you exit.",
        "Dernière version : {version}\n\nTélécharger le package maintenant ?\n"
        "Le package est mis en attente en arrière-plan sans remplacer le moteur actuel, "
        "aucune conversion n'est interrompue. L'installation se fait à la fermeture.",
        "最新バージョン: {version}\n\n更新パッケージを今すぐダウンロードしますか？\n"
        "パッケージはバックグラウンドでダウンロード・ステージングされ、実行中のエンジンを置き換えないため、"
        "変換タスクは中断されません。プログラム終了後に自動インストールされます。",
        "Последняя версия: {version}\n\nСкачать пакет обновления сейчас?\n"
        "Пакет скачивается в фон без замены работающего движка, "
        "поэтому задачи не прерываются. Установка — при выходе из программы.",
        "Última versión: {version}\n\n¿Descargar el paquete de actualización ahora?\n"
        "El paquete se descarga en segundo plano sin reemplazar el motor en uso, "
        "por lo que no se interrumpen las conversiones. Se instala automáticamente al salir.",
    ),
    "settings.ffmpeg.dialog_new_version.btn_download": (
        "立即下载", "Download now", "Download now",
        "Télécharger maintenant", "今すぐダウンロード",
        "Скачать сейчас", "Descargar ahora",
    ),
    "settings.ffmpeg.info_check_failed.title": (
        "更新检查失败", "Update check failed",
        "Update check failed",
        "Échec de la vérification", "更新確認に失敗",
        "Проверка обновлений не удалась", "Error al buscar actualizaciones",
    ),
    "settings.ffmpeg.info_already_latest.title": (
        "当前已是最新版本", "Already up to date",
        "Already up to date",
        "Déjà à jour", "最新バージョンです",
        "Уже последняя версия", "Ya está actualizado",
    ),
    "settings.ffmpeg.info_install_done.title": (
        "安装完成", "Installation complete",
        "Installation complete",
        "Installation terminée", "インストール完了",
        "Установка завершена", "Instalación completada",
    ),
    "settings.ffmpeg.info_install_failed.title": (
        "安装失败", "Installation failed",
        "Installation failed",
        "Échec de l'installation", "インストール失敗",
        "Установка не удалась", "Error de instalación",
    ),
    "settings.ffmpeg.info_staged.title": (
        "更新包已就绪", "Update package ready",
        "Update package ready",
        "Mise à jour prête", "更新パッケージ準備完了",
        "Пакет обновления готов", "Paquete de actualización listo",
    ),
    "settings.ffmpeg.info_stage_failed.title": (
        "更新包下载失败", "Update package download failed",
        "Update package download failed",
        "Échec du téléchargement de la mise à jour",
        "更新パッケージのダウンロードに失敗",
        "Не удалось скачать пакет обновления",
        "Error al descargar el paquete de actualización",
    ),
    "settings.ffmpeg.info_exception.title": (
        "发生异常", "An exception occurred",
        "An exception occurred",
        "Une exception s'est produite", "例外が発生しました",
        "Возникло исключение", "Se produjo una excepción",
    ),
    "settings.ffmpeg.dialog_choose_exe": (
        "选择 ffmpeg.exe", "Select ffmpeg.exe",
        "Select ffmpeg.exe",
        "Sélectionner ffmpeg.exe", "ffmpeg.exeを選択",
        "Выберите ffmpeg.exe", "Seleccionar ffmpeg.exe",
    ),
    "settings.ffmpeg.dialog_exe_filter": (
        "可执行文件 (ffmpeg.exe);;所有文件 (*.*)",
        "Executables (ffmpeg.exe);;All files (*.*)",
        "Executables (ffmpeg.exe);;All files (*.*)",
        "Exécutables (ffmpeg.exe);;Tous les fichiers (*.*)",
        "実行ファイル (ffmpeg.exe);;すべてのファイル (*.*)",
        "Исполняемые файлы (ffmpeg.exe);;Все файлы (*.*)",
        "Ejecutables (ffmpeg.exe);;Todos los archivos (*.*)",
    ),

    # ---------------------------------------------------- settings.hw.*
    "settings.hw.title": (
        "启用硬件加速", "Enable hardware acceleration",
        "Enable hardware acceleration",
        "Activer l'accélération matérielle",
        "ハードウェアアクセラレーションを有効化",
        "Включить аппаратное ускорение",
        "Activar aceleración por hardware",
    ),
    "settings.hw.desc": (
        "自动检测核芯 / 独立显卡与处理器，使用 NVENC、Quick Sync、AMF 或 "
        "Media Foundation 加速编解码；不支持时自动回退 CPU 软件编码",
        "Auto-detects integrated / discrete GPUs and processors, using NVENC, "
        "Quick Sync, AMF or Media Foundation to accelerate encoding. "
        "Falls back to CPU software encoding when unavailable.",
        "Auto-detects integrated / discrete GPUs and processors, using NVENC, "
        "Quick Sync, AMF or Media Foundation to accelerate encoding. "
        "Falls back to CPU software encoding when unavailable.",
        "Détecte automatiquement les GPU intégrés / discrets et le processeur, "
        "utilise NVENC, Quick Sync, AMF ou Media Foundation pour accélérer "
        "l'encodage. Bascule sur CPU logiciel si indisponible.",
        "統合 / 外付け GPU とプロセッサーを自動検出し、NVENC、Quick Sync、AMF または "
        "Media Foundation でエンコードを高速化します。非対応の場合は CPU ソフトウェアエンコードにフォールバックします。",
        "Автоопределение встроенных / дискретных GPU и процессоров, "
        "использование NVENC, Quick Sync, AMF или Media Foundation "
        "для ускорения кодирования. Откат к CPU при отсутствии поддержки.",
        "Detecta automáticamente GPU integradas / discretas y procesadores, "
        "usando NVENC, Quick Sync, AMF o Media Foundation para acelerar la codificación. "
        "Recurre a CPU por software si no está disponible.",
    ),
    "settings.hw.detecting": (
        "正在检测硬件配置…", "Detecting hardware configuration…",
        "Detecting hardware configuration…",
        "Détection de la configuration matérielle…",
        "ハードウェア構成を検出しています…",
        "Определение конфигурации оборудования…",
        "Detectando configuración de hardware…",
    ),
    "settings.hw.redetecting": (
        "正在重新检测硬件并实测编码器能力，请稍候…",
        "Re-detecting hardware and benchmarking encoder capabilities, please wait…",
        "Re-detecting hardware and benchmarking encoder capabilities, please wait…",
        "Redétection du matériel et test des encodeurs, veuillez patienter…",
        "ハードウェアを再検出しエンコーダー能力を実測しています。お待ちください…",
        "Повторное определение оборудования и тестирование энкодеров, подождите…",
        "Volviendo a detectar hardware y probando codificadores, espere…",
    ),
    "settings.hw.btn_redetect": (
        "重新检测硬件", "Re-detect hardware",
        "Re-detect hardware",
        "Redétecter le matériel", "ハードウェアを再検出",
        "Перепроверить оборудование", "Volver a detectar hardware",
    ),
    "settings.hw.info_in_progress.title": (
        "硬件检测进行中", "Hardware detection in progress",
        "Hardware detection in progress",
        "Détection matérielle en cours",
        "ハードウェア検出中",
        "Определение оборудования выполняется",
        "Detección de hardware en curso",
    ),
    "settings.hw.info_in_progress.content": (
        "请等待当前检测完成", "Please wait for the current detection to finish",
        "Please wait for the current detection to finish",
        "Veuillez attendre la fin de la détection en cours",
        "現在の検出が完了するまでお待ちください",
        "Дождитесь завершения текущего определения",
        "Espere a que termine la detección actual",
    ),
    "settings.hw.disabled_note": (
        "（硬件加速开关已关闭：当前全部使用 CPU 软件编码）",
        "(Hardware acceleration is off: all encoding uses CPU software)",
        "(Hardware acceleration is off: all encoding uses CPU software)",
        "(L'accélération matérielle est désactivée : tout l'encodage utilise le CPU)",
        "（ハードウェアアクセラレーションはオフです。現在すべて CPU ソフトウェアエンコードを使用）",
        "(Аппаратное ускорение выключено: всё кодирование на CPU)",
        "(La aceleración por hardware está desactivada: toda la codificación usa CPU)",
    ),

    # ---------------------------------------------------- settings.appearance.*
    "settings.appearance.title": (
        "外观", "Appearance", "Appearance",
        "Apparence", "外観",
        "Внешний вид", "Apariencia",
    ),
    "settings.appearance.theme_auto": (
        "跟随系统", "Follow system", "Follow system",
        "Suivre le système", "システムに合わせる",
        "По системе", "Seguir sistema",
    ),
    "settings.appearance.theme_light": (
        "浅色", "Light", "Light",
        "Clair", "ライト", "Светлая", "Claro",
    ),
    "settings.appearance.theme_dark": (
        "深色", "Dark", "Dark",
        "Sombre", "ダーク", "Тёмная", "Oscuro",
    ),

    # ---------------------------------------------------- settings.network.*
    "settings.network.title": (
        "启动时静默检查 FFmpeg 更新",
        "Silently check for FFmpeg updates on startup",
        "Silently check for FFmpeg updates on startup",
        "Vérifier silencieusement les mises à jour FFmpeg au démarrage",
        "起動時に FFmpegの更新をサイレント確認",
        "Тихо проверять обновления FFmpeg при запуске",
        "Buscar actualizaciones de FFmpeg silenciosamente al iniciar",
    ),
    "settings.network.desc": (
        "发现新版本仅在后台自动下载暂存，退出程序后才安装，不打断转换任务",
        "New versions are downloaded and staged silently in the background, "
        "installed only on exit, without interrupting conversions",
        "New versions are downloaded and staged silently in the background, "
        "installed only on exit, without interrupting conversions",
        "Les nouvelles versions sont téléchargées en arrière-plan et installées "
        "à la fermeture, sans interrompre les conversions",
        "新バージョンはバックグラウンドでダウンロード・ステージングされ、終了時にインストールされます。変換タスクは中断されません",
        "Новые версии скачиваются в фон и устанавливаются при выходе, "
        "не прерывая конвертацию",
        "Las nuevas versiones se descargan en segundo plano y se instalan al salir, "
        "sin interrumpir las conversiones",
    ),
    "settings.network.channel_auto": (
        "自动测速（选择延迟最低的源）",
        "Auto speed test (pick the lowest-latency source)",
        "Auto speed test (pick the lowest-latency source)",
        "Test de débit automatique (source la plus rapide)",
        "自動測速（遅延が最も低いソースを選択）",
        "Автотест скорости (источник с минимальной задержкой)",
        "Prueba de velocidad automática (origen con menor latencia)",
    ),
    "settings.network.channel_direct": (
        "GitHub 官方源（直连）",
        "GitHub official source (direct)",
        "GitHub official source (direct)",
        "Source officielle GitHub (directe)",
        "GitHub 公式ソース（直接接続）",
        "Официальный источник GitHub (прямое подключение)",
        "Fuente oficial de GitHub (directo)",
    ),
    "settings.network.channel_ghfast": (
        "ghfast.top 大陆加速",
        "ghfast.top mainland accelerator",
        "ghfast.top mainland accelerator",
        "ghfast.top accélérateur Chine continentale",
        "ghfast.top 中国大陸アクセラレータ",
        "ghfast.top ускоритель для материкового Китая",
        "ghfast.top acelerador continental",
    ),
    "settings.network.channel_ghproxy": (
        "gh-proxy.com 大陆加速",
        "gh-proxy.com mainland accelerator",
        "gh-proxy.com mainland accelerator",
        "gh-proxy.com accélérateur Chine continentale",
        "gh-proxy.com 中国大陸アクセラレータ",
        "gh-proxy.com ускоритель для материкового Китая",
        "gh-proxy.com acelerador continental",
    ),
    "settings.network.channel_moeyy": (
        "github.moeyy.xyz 大陆加速",
        "github.moeyy.xyz mainland accelerator",
        "github.moeyy.xyz mainland accelerator",
        "github.moeyy.xyz accélérateur Chine continentale",
        "github.moeyy.xyz 中国大陸アクセラレータ",
        "github.moeyy.xyz ускоритель для материкового Китая",
        "github.moeyy.xyz acelerador continental",
    ),
    "settings.network.channel_title": (
        "GitHub 下载通道", "GitHub download channel",
        "GitHub download channel",
        "Canal de téléchargement GitHub",
        "GitHub ダウンロードチャネル",
        "Канал загрузки GitHub", "Canal de descarga de GitHub",
    ),
    "settings.network.channel_desc": (
        "每次下载前对全部可用源做延迟测速；大陆加速源可显著提升更新成功率",
        "Latency-tests all available sources before each download; "
        "mainland accelerators significantly improve update success rates",
        "Latency-tests all available sources before each download; "
        "mainland accelerators significantly improve update success rates",
        "Teste la latence de toutes les sources avant chaque téléchargement ; "
        "les accélérateurs continentaux améliorent nettement le taux de réussite",
        "ダウンロード前にすべての利用可能ソースの遅延を測定します。"
        "中国大陸アクセラレータは更新成功率を大幅に向上させます",
        "Тестирует задержку всех источников перед каждой загрузкой. "
        "Ускорители для материкового Китая значительно повышают成功率",
        "Prueba la latencia de todos los orígenes antes de cada descarga; "
        "los aceleradores continentales mejoran significativamente el éxito de actualización",
    ),

    # ---------------------------------------------------- settings.about.*
    "settings.about.title": (
        "关于", "About", "About",
        "À propos", "情報", "Acerca de", "Acerca de",
    ),
    "settings.about.version_display": (
        "{app} v{version}", "{app} v{version}", "{app} v{version}",
        "{app} v{version}", "{app} v{version}",
        "{app} v{version}", "{app} v{version}",
    ),
    "settings.about.attribution": (
        "本程序使用 FFmpeg（https://ffmpeg.org，LGPL/GPL）进行媒体转换；\n"
        "界面基于 PySide6 与 PyQt-Fluent-Widgets 构建。",
        "This app uses FFmpeg (https://ffmpeg.org, LGPL/GPL) for media conversion;\n"
        "the UI is built with PySide6 and PyQt-Fluent-Widgets.",
        "This app uses FFmpeg (https://ffmpeg.org, LGPL/GPL) for media conversion;\n"
        "the UI is built with PySide6 and PyQt-Fluent-Widgets.",
        "Ce programme utilise FFmpeg (https://ffmpeg.org, LGPL/GPL) pour la conversion ;\n"
        "l'interface est construite avec PySide6 et PyQt-Fluent-Widgets.",
        "本プログラムは FFmpeg（https://ffmpeg.org、LGPL/GPL）を使用してメディア変換を行います。\n"
        "UI は PySide6 および PyQt-Fluent-Widgets で構築されています。",
        "Программа использует FFmpeg (https://ffmpeg.org, LGPL/GPL) для конвертации;\n"
        "интерфейс построен на PySide6 и PyQt-Fluent-Widgets.",
        "Este programa usa FFmpeg (https://ffmpeg.org, LGPL/GPL) para la conversión;\n"
        "la interfaz está construida con PySide6 y PyQt-Fluent-Widgets.",
    ),
    "settings.about.about_ffmpeg_btn": (
        "关于 FFmpeg（介绍 / 版本 / 许可证 / 链接）",
        "About FFmpeg (intro / version / license / links)",
        "About FFmpeg (intro / version / license / links)",
        "À propos de FFmpeg (intro / version / licence / liens)",
        "FFmpegについて（概要 / バージョン / ライセンス / リンク）",
        "О FFmpeg (описание / версия / лицензия / ссылки)",
        "Acerca de FFmpeg (introducción / versión / licencia / enlaces)",
    ),

    # ---------------------------------------------------- settings.app_update.*
    "settings.app_update.btn_check": (
        "检查 Prism 更新", "Check for Prism Updates",
        "Check for Prism Updates",
        "Vérifier les mises à jour de Prism",
        "Prismのアップデートを確認",
        "Проверить обновления Prism",
        "Buscar actualizaciones de Prism",
    ),
    "settings.app_update.btn_install": (
        "安装更新", "Install Update", "Install Update",
        "Installer la mise à jour",
        "アップデートをインストール",
        "Установить обновление",
        "Instalar actualización",
    ),
    "settings.app_update.btn_download_version": (
        "下载 v{version}", "Download v{version}", "Download v{version}",
        "Télécharger v{version}",
        "ダウンロード v{version}",
        "Скачать v{version}",
        "Descargar v{version}",
    ),
    "settings.app_update.caption_connecting": (
        "正在连接 GitHub 检查更新…",
        "Connecting to GitHub to check for updates…",
        "Connecting to GitHub to check for updates…",
        "Connexion à GitHub pour vérifier les mises à jour…",
        "GitHubに接続してアップデートを確認中…",
        "Подключение к GitHub для проверки обновлений…",
        "Conectando a GitHub para buscar actualizaciones…",
    ),
    "settings.app_update.caption_preparing_download": (
        "正在准备下载…", "Preparing download…",
        "Preparing download…",
        "Préparation du téléchargement…",
        "ダウンロードを準備中…",
        "Подготовка загрузки…",
        "Preparando descarga…",
    ),
    "settings.app_update.dialog_new_version.title": (
        "发现新版本", "New Version Available",
        "New Version Available",
        "Nouvelle version disponible",
        "新しいバージョンがあります",
        "Доступна новая версия",
        "Nueva versión disponible",
    ),
    "settings.app_update.dialog_new_version.btn_download": (
        "下载", "Download", "Download",
        "Télécharger", "ダウンロード",
        "Скачать", "Descargar",
    ),
    "settings.app_update.dialog_install.title": (
        "安装更新", "Install Update", "Install Update",
        "Installer la mise à jour",
        "アップデートをインストール",
        "Установить обновление",
        "Instalar actualización",
    ),
    "settings.app_update.dialog_install.content": (
        "安装程序将关闭当前 Prism 并替换为新版本，是否继续？",
        "The installer will close Prism and replace it with the new version. Continue?",
        "The installer will close Prism and replace it with the new version. Continue?",
        "Le programme d'installation fermera Prism et le remplacera. Continuer ?",
        "インストーラーはPrismを閉じて新しいバージョンに置き換えます。続行しますか？",
        "Программа установки закроет Prism и заменит его новой версией. Продолжить?",
        "El instalador cerrará Prism y lo reemplazará. ¿Continuar?",
    ),
    "settings.app_update.dialog_install.btn_install": (
        "安装并退出", "Install & Exit",
        "Install & Exit",
        "Installer et quitter",
        "インストールして終了",
        "Установить и выйти",
        "Instalar y salir",
    ),
    "settings.app_update.info_check_failed.title": (
        "检查失败", "Check Failed", "Check Failed",
        "Échec de la vérification",
        "確認失敗",
        "Ошибка проверки",
        "Error en la verificación",
    ),
    "settings.app_update.info_already_latest.title": (
        "已是最新版本", "Already Latest",
        "Already Latest",
        "Déjà à jour",
        "最新です",
        "Уже последняя версия",
        "Ya actualizado",
    ),
    "settings.app_update.info_download_done.title": (
        "下载完成", "Download Complete",
        "Download Complete",
        "Téléchargement terminé",
        "ダウンロード完了",
        "Загрузка завершена",
        "Descarga completa",
    ),
    "settings.app_update.info_download_failed.title": (
        "下载失败", "Download Failed",
        "Download Failed",
        "Échec du téléchargement",
        "ダウンロード失敗",
        "Ошибка загрузки",
        "Error en la descarga",
    ),
    "settings.app_update.info_installing.title": (
        "正在启动安装程序", "Starting Installer",
        "Starting Installer",
        "Démarrage du programme d'installation",
        "インストーラーを起動中",
        "Запуск программы установки",
        "Iniciando instalador",
    ),
    "settings.app_update.info_installing.content": (
        "安装程序已启动，请保存当前工作并按提示完成安装。",
        "The installer has started. Please save your work and follow the prompts.",
        "The installer has started. Please save your work and follow the prompts.",
        "Le programme d'installation a démarré. Veuillez enregistrer votre travail.",
        "インストーラーが起動しました。作業を保存し、指示に従ってください。",
        "Программа установки запущена. Сохраните работу и следуйте инструкциям.",
        "El instalador se ha iniciado. Guarde su trabajo y siga las instrucciones.",
    ),
    "settings.app_update.info_install_failed.title": (
        "启动失败", "Launch Failed",
        "Launch Failed",
        "Échec du démarrage",
        "起動失敗",
        "Ошибка запуска",
        "Error al iniciar",
    ),
    "settings.app_update.info_install_failed.content": (
        "无法启动安装程序，请手动运行下载的文件。",
        "Could not start the installer. Please run the downloaded file manually.",
        "Could not start the installer. Please run the downloaded file manually.",
        "Impossible de démarrer le programme d'installation. Exécutez le fichier manuellement.",
        "インストーラーを起動できません。ダウンロードしたファイルを手動で実行してください。",
        "Не удалось запустить программу установки. Запустите файл вручную.",
        "No se pudo iniciar el instalador. Ejecute el archivo descargado manualmente.",
    ),

    # ---------------------------------------------------- settings.language.*
    "settings.language.title": (
        "语言", "Language", "Language",
        "Langue", "言語", "Язык", "Idioma",
    ),
    "settings.language.auto": (
        "自动（跟随系统）", "Auto (follow system)",
        "Auto (follow system)",
        "Auto (suivre le système)",
        "自動（システムに合わせる）",
        "Авто (по системе)", "Automático (seguir sistema)",
    ),

    # ---------------------------------------------------- settings.accent.*
    "settings.accent.title": (
        "强调色", "Accent color", "Accent color",
        "Couleur d'accentuation", "アクセントカラー",
        "Акцентный цвет", "Color de acento",
    ),
    "settings.accent.follow_system": (
        "跟随系统", "Follow system", "Follow system",
        "Suivre le système", "システムに合わせる",
        "По системе", "Seguir sistema",
    ),
    "settings.accent.desc": (
        "选择界面中按钮、链接和进度条使用的强调色",
        "Choose the accent color used for buttons, links, and progress bars",
        "Choose the accent color used for buttons, links, and progress bars",
        "Choisissez la couleur d'accentuation des boutons, liens et barres de progression",
        "ボタン、リンク、プログレスバーに使用するアクセントカラーを選択",
        "Выберите акцентный цвет для кнопок, ссылок и прогресс-баров",
        "Elija el color de acento para botones, enlaces y barras de progreso",
    ),
    "settings.accent.custom": (
        "自定义", "Custom", "Custom",
        "Personnalisé", "カスタム",
        "Свой", "Personalizado",
    ),
    "settings.accent.follow_system_label": (
        "跟随系统强调色", "Follow system accent color",
        "Follow system accent color",
        "Suivre la couleur d'accentuation du système",
        "システムのアクセントカラーに合わせる",
        "Использовать системный акцентный цвет",
        "Seguir color de acento del sistema",
    ),
    "settings.accent.follow_system_desc": (
        "自动读取 Windows 个性化设置中的强调色；关闭后可选择自定义颜色",
        "Automatically reads the accent color from Windows personalization; "
        "turn off to choose a custom color",
        "Automatically reads the accent color from Windows personalization; "
        "turn off to choose a custom color",
        "Lit automatiquement la couleur d'accentuation de Windows ; "
        "désactivez pour choisir une couleur personnalisée",
        "Windows のパーソナライズ設定からアクセントカラーを自動取得します。"
        "オフにするとカスタム色を選択できます",
        "Автоматически считывает акцентный цвет из персонализации Windows; "
        "отключите для выбора собственного цвета",
        "Lee automáticamente el color de acento de la personalización de Windows; "
        "desactiva para elegir un color personalizado",
    ),
    "settings.accent.current_system": (
        "当前系统强调色：#{color}",
        "Current system accent: #{color}",
        "Current system accent: #{color}",
        "Couleur d'accentuation système actuelle : #{color}",
        "現在のシステムアクセントカラー：#{color}",
        "Текущий системный акцентный цвет: #{color}",
        "Color de acento del sistema actual: #{color}",
    ),
    "settings.accent.reading_system": (
        "正在读取系统强调色…",
        "Reading system accent color…",
        "Reading system accent color…",
        "Lecture de la couleur d'accentuation du système…",
        "システムアクセントカラーを読み取り中…",
        "Чтение системного акцентного цвета…",
        "Leyendo color de acento del sistema…",
    ),
    "settings.accent.current_custom": (
        "当前自定义颜色：{color}",
        "Current custom color: {color}",
        "Current custom color: {color}",
        "Couleur personnalisée actuelle : {color}",
        "現在のカスタムカラー：{color}",
        "Текущий пользовательский цвет: {color}",
        "Color personalizado actual: {color}",
    ),
    "settings.accent.preset.blue": (
        "微软蓝", "Microsoft Blue", "Microsoft Blue",
        "Bleu Microsoft", "マイクロソフトブルー",
        "Синий Microsoft", "Azul Microsoft",
    ),
    "settings.accent.preset.red": (
        "红", "Red", "Red",
        "Rouge", "赤", "Красный", "Rojo",
    ),
    "settings.accent.preset.orange": (
        "橙", "Orange", "Orange",
        "Orange", "オレンジ", "Оранжевый", "Naranja",
    ),
    "settings.accent.preset.gold": (
        "金", "Gold", "Gold",
        "Or", "ゴールド", "Золотой", "Oro",
    ),
    "settings.accent.preset.green": (
        "绿", "Green", "Green",
        "Vert", "グリーン", "Зелёный", "Verde",
    ),
    "settings.accent.preset.teal": (
        "青绿", "Teal", "Teal",
        "Sarcelle", "ティール", "Бирюзовый", "Verde azulado",
    ),
    "settings.accent.preset.purple": (
        "紫", "Purple", "Purple",
        "Violet", "パープル", "Фиолетовый", "Púrpura",
    ),
    "settings.accent.preset.gray": (
        "灰", "Gray", "Gray",
        "Gris", "グレー", "Серый", "Gris",
    ),
    "settings.language.label": (
        "界面语言", "Interface language", "Interface language",
        "Langue de l'interface", "インターフェース言語",
        "Язык интерфейса", "Idioma de la interfaz",
    ),
    "settings.language.desc": (
        "切换后即时生效；选择「跟随系统」将自动匹配操作系统区域设置",
        "Takes effect immediately; select \"Follow system\" to auto-match the OS locale",
        "Takes effect immediately; select \"Follow system\" to auto-match the OS locale",
        "Prend effet immédiatement ; sélectionnez « Suivre le système » pour correspondre automatiquement aux paramètres régionaux",
        "切替後すぐに反映されます。「システムに合わせる」を選ぶとOSのロケールに自動的に合わせます",
        "Вступает в силу немедленно; выберите «По системе» для автоматического совпадения с языком ОС",
        "Se aplica inmediatamente; selecciona «Seguir sistema» para coincidir automáticamente con la configuración regional del SO",
    ),

    # ---------------------------------------------------- help.*
    "help.title": (
        "帮助与说明", "Help & Guide", "Help & Guide",
        "Aide et guide", "ヘルプとガイド",
        "Справка и руководство", "Ayuda y guía",
    ),
    "help.subtitle": (
        "快速上手指南、支持的格式清单与常见问题",
        "Quick start guide, supported format list and FAQs",
        "Quick start guide, supported format list and FAQs",
        "Guide de démarrage rapide, liste des formats et FAQ",
        "クイックスタートガイド、対応フォーマット一覧、よくある質問",
        "Краткое руководство, список форматов и FAQ",
        "Guía de inicio rápido, lista de formatos y preguntas frecuentes",
    ),
    "help.quick_start.title": (
        "快速开始（四步）", "Quick Start (4 Steps)",
        "Quick Start (4 Steps)",
        "Démarrage rapide (4 étapes)",
        "クイックスタート（4ステップ）",
        "Быстрый старт (4 шага)", "Inicio rápido (4 pasos)",
    ),

    # 步骤
    "help.step.1.title": (
        "添加文件", "Add Files", "Add Files",
        "Ajouter des fichiers", "ファイルを追加",
        "Добавить файлы", "Añadir archivos",
    ),
    "help.step.1.desc": (
        "在“格式转换”页将文件或整个文件夹拖放到虚线区域，也可以点击区域选择文件，支持批量添加。",
        "On the Convert page, drag files or a folder onto the dashed area, "
        "or click the area to pick files. Batch adding is supported.",
        "On the Convert page, drag files or a folder onto the dashed area, "
        "or click the area to pick files. Batch adding is supported.",
        "Sur la page Convertir, glissez des fichiers ou un dossier dans la zone en pointillés, "
        "ou cliquez sur la zone pour choisir des fichiers. Ajout en lot possible.",
        "「フォーマット変換」ページでファイルまたはフォルダー全体を点線エリアにドロップするか、エリアをクリックしてファイルを選択できます。一括追加に対応。",
        "На странице «Конвертация» перетащите файлы или папку в пунктирную область "
        "или щёлкните по области для выбора. Поддерживается пакетное добавление.",
        "En la página Convertir, arrastre archivos o una carpeta al área punteada, "
        "o haga clic en el área para elegir archivos. Se admite añadir en lote.",
    ),
    "help.step.2.title": (
        "选择格式", "Choose Format", "Choose Format",
        "Choisir le format", "フォーマットを選択",
        "Выбрать формат", "Elegir formato",
    ),
    "help.step.2.desc": (
        "通过顶部 视频 / 音频 / 图片 切换分类，再在“输出格式”中选择目标格式与质量预设。视频还可以提取为音频。",
        "Switch the category via the top tabs (Video / Audio / Image), then pick "
        "the target format and quality preset in Output Format. Videos can also be extracted as audio.",
        "Switch the category via the top tabs (Video / Audio / Image), then pick "
        "the target format and quality preset in Output Format. Videos can also be extracted as audio.",
        "Basculez la catégorie via les onglets (Vidéo / Audio / Image), puis choisissez "
        "le format cible et le préréglage dans Format de sortie. Les vidéos peuvent être extraites en audio.",
        "上部の 動画 / 音声 / 画像 タブでカテゴリを切り替え、「出力フォーマット」で出力フォーマットと品質プリセットを選択します。動画から音声を抽出することも可能です。",
        "Переключите категорию через верхние вкладки (Видео / Аудио / Изображение), "
        "затем выберите формат и пресет в «Формат вывода». Видео можно извлечь как аудио.",
        "Cambie la categoría con las pestañas superiores (Vídeo / Audio / Imagen), "
        "luego elija el formato y preset en Formato de salida. Los vídeos también pueden extraerse como audio.",
    ),
    "help.step.3.title": (
        "设置输出", "Configure Output", "Configure Output",
        "Configurer la sortie", "出力を設定",
        "Настроить вывод", "Configurar salida",
    ),
    "help.step.3.desc": (
        "默认输出到源文件所在文件夹，也可以指定统一的输出目录；同名文件支持自动重命名、覆盖或跳过。",
        "By default, output goes to the source folder. You can also set a unified output directory. "
        "Name conflicts can be auto-renamed, overwritten or skipped.",
        "By default, output goes to the source folder. You can also set a unified output directory. "
        "Name conflicts can be auto-renamed, overwritten or skipped.",
        "Par défaut, la sortie va dans le dossier source. Vous pouvez aussi définir un dossier unifié. "
        "Les conflits de noms peuvent être renommés, écrasés ou ignorés.",
        "デフォルトでは元ファイルのフォルダーに出力されます。統一の出力ディレクトリを指定することも可能です。同名ファイルは自動リネーム、上書き、スキップに対応。",
        "По умолчанию вывод идёт в папку исходного файла. Можно задать единую папку вывода. "
        "Совпадающие имена можно авто-переименовать, перезаписать или пропустить.",
        "Por defecto, la salida va a la carpeta de origen. Puede fijar un directorio unificado. "
        "Los conflictos de nombre pueden renombrarse, sobrescribirse u omitirse.",
    ),
    "help.step.4.title": (
        "开始转换", "Start Conversion", "Start Conversion",
        "Démarrer la conversion", "変換を開始",
        "Начать конвертацию", "Iniciar conversión",
    ),
    "help.step.4.desc": (
        "点击“开始转换”，任务自动加入队列并发执行；在“任务队列”页可以查看进度、取消任务或重试失败项。",
        "Click \"Start Conversion\" and tasks are queued and run concurrently. "
        "On the Queue page you can view progress, cancel tasks or retry failures.",
        "Click \"Start Conversion\" and tasks are queued and run concurrently. "
        "On the Queue page you can view progress, cancel tasks or retry failures.",
        "Cliquez sur « Démarrer la conversion » : les tâches sont mises en file et exécutées simultanément. "
        "Sur la page File d'attente, suivez la progression, annulez ou relancez les échecs.",
        "「変換を開始」をクリックするとタスクがキューに登録され並列実行されます。「タスクキュー」画面で進捗確認、タスクのキャンセル、失敗の再試行ができます。",
        "Нажмите «Начать конвертацию» — задачи встанут в очередь и выполнятся параллельно. "
        "На странице «Очередь» можно смотреть прогресс, отменять задачи и повторять сбойные.",
        "Haga clic en «Iniciar conversión»: las tareas se encolan y se ejecutan simultáneamente. "
        "En la página Cola puede ver el progreso, cancelar tareas o reintentar las fallidas.",
    ),

    # 支持格式
    "help.formats.title": (
        "支持的目标格式", "Supported output formats",
        "Supported output formats",
        "Formats de sortie pris en charge",
        "対応する出力フォーマット",
        "Поддерживаемые форматы вывода",
        "Formatos de salida admitidos",
    ),
    "help.formats.video_section": (
        "视频（视频文件可转出，也可提取音频）",
        "Video (can export and extract audio)",
        "Video (can export and extract audio)",
        "Vidéo (export et extraction audio)",
        "動画（動画ファイルの出力および音声抽出に対応）",
        "Видео (экспорт и извлечение аудио)",
        "Vídeo (exportar y extraer audio)",
    ),
    "help.formats.audio_section": (
        "音频", "Audio", "Audio",
        "Audio", "音声", "Аудио", "Audio",
    ),
    "help.formats.image_section": (
        "图片", "Image", "Image",
        "Image", "画像", "Изображение", "Imagen",
    ),
    "help.formats.note": (
        "提示：源格式支持范围更广（如 FLV / RMVB / HEIC / AVIF 等），"
        "FFmpeg 能识别即可作为输入。",
        "Note: input format support is broader (e.g. FLV / RMVB / HEIC / AVIF). "
        "Anything FFmpeg recognizes can be used as input.",
        "Note: input format support is broader (e.g. FLV / RMVB / HEIC / AVIF). "
        "Anything FFmpeg recognizes can be used as input.",
        "Note : les formats d'entrée sont plus larges (ex. FLV / RMVB / HEIC / AVIF). "
        "Tout ce que FFmpeg reconnaît peut servir d'entrée.",
        "ヒント: 入力フォーマットの対応範囲はより広範です（例: FLV / RMVB / HEIC / AVIF など）。"
        "FFmpeg が認識できるものは入力として使用できます。",
        "Примечание: поддерживаемые входные форматы шире (напр. FLV / RMVB / HEIC / AVIF). "
        "Всё, что распознаёт FFmpeg, может быть входом.",
        "Nota: los formatos de entrada son más amplios (p. ej. FLV / RMVB / HEIC / AVIF). "
        "Todo lo que FFmpeg reconozca puede usarse como entrada.",
    ),

    # FFmpeg 引擎卡片
    "help.engine.title": (
        "FFmpeg 转换引擎", "FFmpeg Engine", "FFmpeg Engine",
        "Moteur FFmpeg", "FFmpeg 変換エンジン",
        "Движок FFmpeg", "Motor FFmpeg",
    ),
    "help.engine.desc": (
        "本程序的全部媒体转换能力均由开源的 FFmpeg 提供。可在此查看引擎介绍、"
        "当前内置版本、开源许可证说明与官方文档 / 下载资源链接。",
        "All media conversion capabilities of this app are powered by the open-source FFmpeg. "
        "View the engine introduction, bundled version, license and official resources here.",
        "All media conversion capabilities of this app are powered by the open-source FFmpeg. "
        "View the engine introduction, bundled version, license and official resources here.",
        "Toutes les capacités de conversion de ce programme proviennent de FFmpeg open-source. "
        "Consultez ici l'intro du moteur, la version intégrée, la licence et les ressources officielles.",
        "本プログラムのすべてのメディア変換機能はオープンソースの FFmpeg によって提供されています。"
        "エンジンの概要、内蔵バージョン、オープンソースライセンス、公式ドキュメント / ダウンロードリンクをここで確認できます。",
        "Все возможности конвертации в этом приложении обеспечены открытым FFmpeg. "
        "Здесь — описание движка, встроенная версия, лицензия и официальные ссылки.",
        "Todas las capacidades de conversión de esta app provienen del FFmpeg de código abierto. "
        "Consulte aquí la introducción del motor, versión integrada, licencia y recursos oficiales.",
    ),
    "help.engine.about_btn": (
        "关于 FFmpeg", "About FFmpeg", "About FFmpeg",
        "À propos de FFmpeg", "FFmpegについて",
        "О FFmpeg", "Acerca de FFmpeg",
    ),

    # FAQ
    "help.faq.title": (
        "常见问题", "FAQ", "FAQ",
        "FAQ", "よくある質問", "Частые вопросы", "Preguntas frecuentes",
    ),
    "help.faq.q_prefix": (
        "Q：", "Q: ", "Q: ", "Q : ", "Q：", "В: ", "P: ",
    ),
    "help.faq.a_prefix": (
        "A：", "A: ", "A: ", "R : ", "A：", "О: ", "R: ",
    ),

    "help.faq.1.q": (
        "支持哪些格式？", "What formats are supported?",
        "What formats are supported?",
        "Quels formats sont pris en charge ?",
        "対応フォーマットは？", "Какие форматы поддерживаются?",
        "¿Qué formatos se admiten?",
    ),
    "help.faq.1.a": (
        "覆盖 MP3 / WAV / FLAC / AAC / OGG / OPUS / WMA 等音频，"
        "MP4 / MKV / AVI / MOV / WEBM / GIF 等视频，"
        "以及 JPG / PNG / WEBP / BMP / TIFF / ICO 等图片。"
        "实际能力由内置 FFmpeg 提供，更新 FFmpeg 即可获得更多编码。",
        "Covers MP3 / WAV / FLAC / AAC / OGG / OPUS / WMA audio, "
        "MP4 / MKV / AVI / MOV / WEBM / GIF video, "
        "and JPG / PNG / WEBP / BMP / TIFF / ICO images. "
        "Actual capabilities depend on the bundled FFmpeg; update it for more codecs.",
        "Covers MP3 / WAV / FLAC / AAC / OGG / OPUS / WMA audio, "
        "MP4 / MKV / AVI / MOV / WEBM / GIF video, "
        "and JPG / PNG / WEBP / BMP / TIFF / ICO images. "
        "Actual capabilities depend on the bundled FFmpeg; update it for more codecs.",
        "Couvre MP3 / WAV / FLAC / AAC / OGG / OPUS / WMA audio, "
        "MP4 / MKV / AVI / MOV / WEBM / GIF vidéo, "
        "et JPG / PNG / WEBP / BMP / TIFF / ICO images. "
        "Les capacités réelles dépendent du FFmpeg intégré ; mettez-le à jour pour plus de codecs.",
        "MP3 / WAV / FLAC / AAC / OGG / OPUS / WMA などの音声、"
        "MP4 / MKV / AVI / MOV / WEBM / GIF などの動画、"
        "JPG / PNG / WEBP / BMP / TIFF / ICO などの画像に対応。"
        "実際の対応能力は内蔵 FFmpeg に依存します。FFmpeg を更新することでより多くのコーデックが利用可能になります。",
        "Поддерживает MP3 / WAV / FLAC / AAC / OGG / OPUS / WMA аудио, "
        "MP4 / MKV / AVI / MOV / WEBM / GIF видео, "
        "и JPG / PNG / WEBP / BMP / TIFF / ICO изображения. "
        "Реальные возможности зависят от встроенного FFmpeg; обновите для большего числа кодеков.",
        "Cubre MP3 / WAV / FLAC / AAC / OGG / OPUS / WMA audio, "
        "MP4 / MKV / AVI / MOV / WEBM / GIF vídeo, "
        "y JPG / PNG / WEBP / BMP / TIFF / ICO imágenes. "
        "Las capacidades reales dependen del FFmpeg integrado; actualícelo para más códecs.",
    ),
    "help.faq.2.q": (
        "第一次打开提示“未安装 FFmpeg”？",
        "First launch shows \"FFmpeg not installed\"?",
        "First launch shows \"FFmpeg not installed\"?",
        "Au premier lancement, « FFmpeg non installé » ?",
        "初回起動時に「FFmpeg未インストール」と表示される？",
        "При первом запуске пишет «FFmpeg не установлен»?",
        "¿Al primer inicio muestra «FFmpeg no instalado»?",
    ),
    "help.faq.2.a": (
        "前往“设置”页面点击“下载内置 FFmpeg”，程序会自动下载、校验并安装，无需手动配置环境变量。",
        "Go to Settings and click \"Download bundled FFmpeg\". The app will download, "
        "verify and install it automatically — no manual environment setup needed.",
        "Go to Settings and click \"Download bundled FFmpeg\". The app will download, "
        "verify and install it automatically — no manual environment setup needed.",
        "Allez dans Paramètres et cliquez « Télécharger FFmpeg intégré ». "
        "Le programme télécharge, vérifie et installe automatiquement, sans configuration manuelle.",
        "「設定」ページで「内蔵 FFmpegをダウンロード」をクリックしてください。"
        "プログラムが自動でダウンロード・検証・インストールします。環境変数の手動設定は不要です。",
        "Перейдите в «Настройки» и нажмите «Скачать встроенный FFmpeg». "
        "Программа скачает, проверит и установит его автоматически — ручная настройка не нужна.",
        "Vaya a Ajustes y haga clic en «Descargar FFmpeg integrado». "
        "La app descargará, verificará e instalará automáticamente, sin configurar variables de entorno.",
    ),
    "help.faq.3.q": (
        "中文、空格或长路径会失败吗？",
        "Will Chinese characters, spaces or long paths fail?",
        "Will Chinese characters, spaces or long paths fail?",
        "Les caractères chinois, espaces ou chemins longs causent-ils des échecs ?",
        "中国語、スペース、長いパスで失敗しますか？",
        "Китайские символы, пробелы или длинные пути вызовут сбой?",
        "¿Fallan los caracteres chinos, espacios o rutas largas?",
    ),
    "help.faq.3.a": (
        "不会。所有转换均以参数列表方式调用 FFmpeg，完整支持中文、空格和超长路径。",
        "No. All conversions invoke FFmpeg via an argument list, fully supporting "
        "Chinese characters, spaces and very long paths.",
        "No. All conversions invoke FFmpeg via an argument list, fully supporting "
        "Chinese characters, spaces and very long paths.",
        "Non. Toutes les conversions appellent FFmpeg via une liste d'arguments, "
        "prenant en charge les caractères chinois, espaces et chemins longs.",
        "いいえ。すべての変換は引数リスト方式で FFmpeg を呼び出すため、"
        "中国語、スペース、超長パスに完全対応しています。",
        "Нет. Все конвертации вызывают FFmpeg через список аргументов, "
        "полностью поддерживая китайские символы, пробелы и сверхдлинные пути.",
        "No. Todas las conversiones invocan FFmpeg mediante una lista de argumentos, "
        "con soporte completo de caracteres chinos, espacios y rutas muy largas.",
    ),
    "help.faq.4.q": (
        "转换速度由什么决定？",
        "What determines conversion speed?",
        "What determines conversion speed?",
        "Qu'est-ce qui détermine la vitesse de conversion ?",
        "変換速度は何で決まりますか？",
        "Что определяет скорость конвертации?",
        "¿Qué determina la velocidad de conversión?",
    ),
    "help.faq.4.a": (
        "主要取决于视频编码、分辨率、质量预设和硬件性能。程序会自动识别 NVIDIA / Intel / AMD 显卡并启用 "
        "NVENC / Quick Sync / AMF 硬件编码，ARM 设备使用 Media Foundation；"
        "可在“设置”中查看或关闭硬件加速。",
        "Mainly determined by codec, resolution, quality preset and hardware. "
        "The app auto-detects NVIDIA / Intel / AMD GPUs and enables NVENC / Quick Sync / AMF "
        "hardware encoding; ARM devices use Media Foundation. "
        "Hardware acceleration can be toggled in Settings.",
        "Mainly determined by codec, resolution, quality preset and hardware. "
        "The app auto-detects NVIDIA / Intel / AMD GPUs and enables NVENC / Quick Sync / AMF "
        "hardware encoding; ARM devices use Media Foundation. "
        "Hardware acceleration can be toggled in Settings.",
        "Dépend principalement du codec, de la résolution, du préréglage et du matériel. "
        "L'appli détecte NVIDIA / Intel / AMD et active NVENC / Quick Sync / AMF ; "
        "les appareils ARM utilisent Media Foundation. "
        "L'accélération matérielle peut être désactivée dans les Paramètres.",
        "主に動画コーデック、解像度、品質プリセット、ハードウェア性能によって決まります。"
        "プログラムは NVIDIA / Intel / AMD グラフィックを自動認識し、"
        "NVENC / Quick Sync / AMF ハードウェアエンコードを有効化します。"
        "ARM デバイスでは Media Foundation を使用します。"
        "「設定」でハードウェアアクセラレーションを確認・切り替えできます。",
        "Главным образом — кодеком, разрешением, пресетом и оборудованием. "
        "Программа автоопределяет NVIDIA / Intel / AMD и включает NVENC / Quick Sync / AMF; "
        "ARM-устройства используют Media Foundation. "
        "Аппаратное ускорение можно отключить в «Настройках».",
        "Depende principalmente del códec, resolución, preset de calidad y hardware. "
        "La app detecta automáticamente NVIDIA / Intel / AMD y activa NVENC / Quick Sync / AMF; "
        "los dispositivos ARM usan Media Foundation. "
        "La aceleración por hardware se puede alternar en Ajustes.",
    ),
    "help.faq.5.q": (
        "硬件加速支持哪些设备？",
        "Which devices support hardware acceleration?",
        "Which devices support hardware acceleration?",
        "Quels appareils prennent en charge l'accélération matérielle ?",
        "ハードウェアアクセラレーションに対応するデバイスは？",
        "Какие устройства поддерживают аппаратное ускорение?",
        "¿Qué dispositivos admiten aceleración por hardware?",
    ),
    "help.faq.5.a": (
        "支持 Intel 与 AMD 核芯显卡，Intel / AMD / NVIDIA 独立显卡，"
        "以及 Windows on ARM 平台的 GPU 加速；"
        "启动时通过系统接口自动检测，并对编码器做实际编码验证，"
        "不可用时自动回退 CPU 软件编码。",
        "Supports Intel and AMD integrated graphics, Intel / AMD / NVIDIA discrete GPUs, "
        "and Windows on ARM GPU acceleration. "
        "Auto-detected via system APIs at startup with real encoding validation; "
        "falls back to CPU software encoding when unavailable.",
        "Supports Intel and AMD integrated graphics, Intel / AMD / NVIDIA discrete GPUs, "
        "and Windows on ARM GPU acceleration. "
        "Auto-detected via system APIs at startup with real encoding validation; "
        "falls back to CPU software encoding when unavailable.",
        "Prend en charge les graphiques intégrés Intel et AMD, les GPU discrets Intel / AMD / NVIDIA, "
        "et l'accélération GPU Windows on ARM. "
        "Détection automatique au démarrage avec validation réelle de l'encodage ; "
        "bascule sur CPU logiciel si indisponible.",
        "Intel および AMD の統合グラフィック、Intel / AMD / NVIDIA の外付け GPU、"
        "Windows on ARM プラットフォームの GPU アクセラレーションに対応。"
        "起動時にシステム API で自動検出し、エンコーダーの実エンコード検証を行います。"
        "利用不可の場合は CPU ソフトウェアエンコードに自動フォールバックします。",
        "Поддерживает встроенную графику Intel и AMD, дискретные GPU Intel / AMD / NVIDIA, "
        "и GPU-ускорение Windows on ARM. "
        "Автоопределение через системные API при запуске с реальным тестированием кодирования; "
        "откат к CPU при отсутствии поддержки.",
        "Admite gráficos integrados de Intel y AMD, GPU discretas Intel / AMD / NVIDIA, "
        "y aceleración GPU de Windows on ARM. "
        "Detección automática al iniciar con validación real de codificación; "
        "recurre a CPU por software si no está disponible.",
    ),
    "help.faq.6.q": (
        "视频分辨率和帧率可以调整吗？",
        "Can video resolution and frame rate be adjusted?",
        "Can video resolution and frame rate be adjusted?",
        "Peut-on ajuster la résolution et le débit d'images ?",
        "動画の解像度とフレームレートは調整できますか？",
        "Можно ли менять разрешение и частоту кадров видео?",
        "¿Se pueden ajustar la resolución y la tasa de fotogramas del vídeo?",
    ),
    "help.faq.6.a": (
        "可以。输出设置支持最高 4K UHD（3840×2160）的分辨率压缩（仅缩小不放大），"
        "帧率提供 24 / 25 / 30 / 50 / 60 fps 预设，GIF 的帧率由质量预设决定。",
        "Yes. Output settings support up to 4K UHD (3840×2160) downscaling (downscale only). "
        "Frame rate presets include 24 / 25 / 30 / 50 / 60 fps. "
        "GIF frame rate is determined by the quality preset.",
        "Yes. Output settings support up to 4K UHD (3840×2160) downscaling (downscale only). "
        "Frame rate presets include 24 / 25 / 30 / 50 / 60 fps. "
        "GIF frame rate is determined by the quality preset.",
        "Oui. Les paramètres de sortie prennent en charge la réduction jusqu'à 4K UHD (3840×2160) "
        "(réduction uniquement). Les débits proposés sont 24 / 25 / 30 / 50 / 60 fps. "
        "Le débit GIF est déterminé par le préréglage qualité.",
        "はい。出力設定では最大 4K UHD（3840×2160）までの解像度圧縮（縮小のみ）に対応し、"
        "フレームレートは 24 / 25 / 30 / 50 / 60 fps のプリセットを用意。"
        "GIF のフレームレートは品質プリセットで決定されます。",
        "Да. Настройки вывода поддерживают сжатие до 4K UHD (3840×2160) (только уменьшение). "
        "Пресеты частоты кадров: 24 / 25 / 30 / 50 / 60 fps. "
        "Частота кадров GIF определяется пресетом качества.",
        "Sí. Los ajustes de salida admiten reducción hasta 4K UHD (3840×2160) (solo reducir). "
        "Los presets de tasa de fotogramas son 24 / 25 / 30 / 50 / 60 fps. "
        "La tasa del GIF la determina el preset de calidad.",
    ),
    "help.faq.7.q": (
        "GIF 转换为什么比较慢？",
        "Why is GIF conversion relatively slow?",
        "Why is GIF conversion relatively slow?",
        "Pourquoi la conversion GIF est-elle lente ?",
        "GIF 変換が遅いのはなぜですか？",
        "Почему конвертация в GIF относительно медленная?",
        "¿Por qué la conversión a GIF es lenta?",
    ),
    "help.faq.7.a": (
        "为保证画质，视频转 GIF 采用“先生成优化调色板、再合成”的两步流程，属于正常现象。",
        "To preserve quality, video-to-GIF uses a two-pass process: "
        "generate an optimized palette first, then compose. This is normal.",
        "To preserve quality, video-to-GIF uses a two-pass process: "
        "generate an optimized palette first, then compose. This is normal.",
        "Pour préserver la qualité, la conversion vidéo vers GIF utilise un processus en deux passes : "
        "générer une palette optimisée, puis composer. C'est normal.",
        "画質を維持するため、動画から GIF への変換では「最適化パレットを生成してから合成する」"
        "2 ステップ方式を採用しています。正常な動作です。",
        "Для сохранения качества видео-в-GIF использует двухпроходный процесс: "
        "сначала генерация оптимизированной палитры, затем合成. Это нормально.",
        "Para preservar la calidad, la conversión de vídeo a GIF usa un proceso de dos pasadas: "
        "generar una paleta optimizada y luego componer. Es normal.",
    ),
    "help.faq.8.q": (
        "转换失败怎么办？",
        "What if conversion fails?",
        "What if conversion fails?",
        "Que faire en cas d'échec de conversion ?",
        "変換に失敗したらどうすれば？",
        "Что делать при сбое конвертации?",
        "¿Qué hago si la conversión falla?",
    ),
    "help.faq.8.a": (
        "在任务状态上悬停可查看 FFmpeg 的具体报错；可直接点击重试按钮。"
        "缺少编码器等问题可在设置中更新 FFmpeg。",
        "Hover over the task status to see the specific FFmpeg error; "
        "click the retry button directly. Missing codec issues can be resolved "
        "by updating FFmpeg in Settings.",
        "Hover over the task status to see the specific FFmpeg error; "
        "click the retry button directly. Missing codec issues can be resolved "
        "by updating FFmpeg in Settings.",
        "Survolez le statut de la tâche pour voir l'erreur FFmpeg ; "
        "cliquez sur le bouton de réessai. Les problèmes de codec manquant "
        "se résolvent en mettant à jour FFmpeg dans les Paramètres.",
        "タスクステータスにカーソルを合わせると FFmpeg の具体的なエラーを確認できます。"
        "再試行ボタンを直接クリック可能です。コーデック不足などの問題は"
        "設定で FFmpeg を更新することで解決できます。",
        "Наведите курсор на статус задачи, чтобы увидеть конкретную ошибку FFmpeg; "
        "нажмите кнопку повтора. Проблемы с отсутствующими кодеками "
        "решаются обновлением FFmpeg в «Настройках».",
        "Pase el cursor sobre el estado de la tarea para ver el error específico de FFmpeg; "
        "haga clic en el botón de reintento. Los problemas de códecs faltantes "
        "se resuelven actualizando FFmpeg en Ajustes.",
    ),

    # ---------------------------------------------------- about_ffmpeg.*
    "about_ffmpeg.title": (
        "关于 FFmpeg", "About FFmpeg", "About FFmpeg",
        "À propos de FFmpeg", "FFmpegについて",
        "О FFmpeg", "Acerca de FFmpeg",
    ),
    "about_ffmpeg.intro": (
        "FFmpeg 是一套领先的跨平台开源音视频处理工具集，提供录制、转码、"
        "封装、流媒体与后期处理的完整能力，是本应用全部媒体转换功能的引擎。\n"
        "Prism 的诞生离不开 FFmpeg 开源项目以及其他开源技术的支持。",
        "FFmpeg is a leading cross-platform open-source audio/video toolkit, offering recording, "
        "transcoding, muxing, streaming and post-processing. It powers all media conversion in this app.\n"
        "Prism would not exist without the FFmpeg open-source project and the support of other "
        "open-source technologies.",
        "FFmpeg is a leading cross-platform open-source audio/video toolkit, offering recording, "
        "transcoding, muxing, streaming and post-processing. It powers all media conversion in this app.\n"
        "Prism would not exist without the FFmpeg open-source project and the support of other "
        "open-source technologies.",
        "FFmpeg est une boîte à outils open-source multiplateforme de référence, "
        "offrant enregistrement, transcodage, multiplexage, streaming et post-traitement. "
        "Elle propulse toutes les conversions de cette appli.\n"
        "Prism doit sa naissance au projet open-source FFmpeg ainsi qu'au soutien d'autres "
        "technologies libres.",
        "FFmpeg はクロスプラットフォームの先進的なオープンソース AV処理ツールキットです。"
        "録音、トランスコード、カプセル化、ストリーミング、ポストプロダクションの完全な機能を提供し、"
        "本アプリのすべてのメディア変換機能のエンジンです。\n"
        "Prism の誕生は FFmpeg オープンソースプロジェクトおよびその他のオープンソース技術の"
        "支えによるものです。",
        "FFmpeg — передовой кроссплатформенный открытый набор инструментов для аудио/видео, "
        "предоставляющий запись, перекодирование, мультиплексирование, стриминг и постобработку. "
        "Он обеспечивает все конвертации в этом приложении.\n"
        "Появление Prism стало возможным благодаря открытому проекту FFmpeg и поддержке других "
        "технологий с открытым исходным кодом.",
        "FFmpeg es un conjunto de herramientas de código abierto multiplataforma y líder, "
        "que ofrece grabación, transcodificación, multiplexación, streaming y posproducción. "
        "Es el motor de todas las conversiones de esta app.\n"
        "Prism no sería posible sin el proyecto de código abierto FFmpeg y el apoyo de otras "
        "tecnologías abiertas.",
    ),
    "about_ffmpeg.version_label": (
        "当前内置版本：FFmpeg {version}\n来源：{source}　·　运行架构：{arch}\n可执行文件：{path}",
        "Bundled version: FFmpeg {version}\nSource: {source}  ·  Architecture: {arch}\nExecutable: {path}",
        "Bundled version: FFmpeg {version}\nSource: {source}  ·  Architecture: {arch}\nExecutable: {path}",
        "Version intégrée : FFmpeg {version}\nSource : {source}  ·  Architecture : {arch}\nExécutable : {path}",
        "内蔵バージョン: FFmpeg {version}\nソース: {source}　·　アーキテクチャ: {arch}\n実行ファイル: {path}",
        "Встроенная версия: FFmpeg {version}\nИсточник: {source}  ·  Архитектура: {arch}\nИсполняемый файл: {path}",
        "Versión integrada: FFmpeg {version}\nOrigen: {source}  ·  Arquitectura: {arch}\nEjecutable: {path}",
    ),
    "about_ffmpeg.license": (
        "许可证：FFmpeg 主要依据 GNU LGPL 2.1 或更高版本发布；"
        "本程序内置的 Windows 构建包含部分 GPL 组件，按 GPL 兼容条款使用。"
        "完整法律声明、源码获取方式与第三方组件清单见官方许可证页面。",
        "License: FFmpeg is primarily released under GNU LGPL 2.1 or later; "
        "the bundled Windows build includes some GPL components, used under GPL-compatible terms. "
        "See the official license page for full legal notices, source access and third-party component list.",
        "License: FFmpeg is primarily released under GNU LGPL 2.1 or later; "
        "the bundled Windows build includes some GPL components, used under GPL-compatible terms. "
        "See the official license page for full legal notices, source access and third-party component list.",
        "Licence : FFmpeg est principalement publié sous GNU LGPL 2.1 ou supérieur ; "
        "la version Windows intégrée contient des composants GPL, utilisés sous des termes compatibles GPL. "
        "Voir la page de licence officielle pour les mentions légales, l'accès au code et la liste des tiers.",
        "ライセンス: FFmpeg は主に GNU LGPL 2.1 以降に基づき公開されています。"
        "本プログラムの内蔵 Windows ビルドには一部 GPL コンポーネントが含まれ、"
        "GPL 互換条項に基づき使用されています。"
        "完全な法的説明、ソースコード取得方法、サードパーティコンポーネント一覧は公式ライセンスページをご覧ください。",
        "Лицензия: FFmpeg в основном выпускается под GNU LGPL 2.1 или новее; "
        "встроенная Windows-сборка содержит некоторые GPL-компоненты, "
        "используемые на условиях, совместимых с GPL. "
        "Полные юридические уведомления, доступ к исходному коду и список сторонних компонентов — на официальной странице лицензии.",
        "Licencia: FFmpeg se publica principalmente bajo GNU LGPL 2.1 o superior; "
        "la compilación de Windows integrada incluye algunos componentes GPL, "
        "usados bajo términos compatibles con GPL. "
        "Consulte la página de licencia oficial para avisos legales, acceso al código y lista de terceros.",
    ),
    "about_ffmpeg.resources": (
        "官方资源", "Official Resources", "Official Resources",
        "Ressources officielles", "公式リソース",
        "Официальные ресурсы", "Recursos oficiales",
    ),
    "about_ffmpeg.link.website": (
        "FFmpeg 官方网站", "FFmpeg official website",
        "FFmpeg official website",
        "Site officiel FFmpeg", "FFmpeg 公式サイト",
        "Официальный сайт FFmpeg", "Sitio oficial de FFmpeg",
    ),
    "about_ffmpeg.link.docs": (
        "官方文档", "Official documentation",
        "Official documentation",
        "Documentation officielle", "公式ドキュメント",
        "Официальная документация", "Documentación oficial",
    ),
    "about_ffmpeg.link.ffmpeg_man": (
        "命令行工具手册（ffmpeg）", "Command-line tool manual (ffmpeg)",
        "Command-line tool manual (ffmpeg)",
        "Manuel de l'outil en ligne de commande (ffmpeg)",
        "コマンドラインツールマニュアル（ffmpeg）",
        "Руководство по CLI-инструменту (ffmpeg)",
        "Manual de la herramienta de línea de comandos (ffmpeg)",
    ),
    "about_ffmpeg.link.download": (
        "官方下载页面", "Official download page",
        "Official download page",
        "Page de téléchargement officielle",
        "公式ダウンロードページ",
        "Официальная страница загрузки",
        "Página de descarga oficial",
    ),
    "about_ffmpeg.link.license": (
        "许可证与法律说明", "License and legal information",
        "License and legal information",
        "Licence et informations légales",
        "ライセンスと法的説明",
        "Лицензия и юридическая информация",
        "Licencia e información legal",
    ),

    # ---------------------------------------------------- task.*
    "task.waiting": (
        "等待中", "Waiting", "Waiting",
        "En attente", "待機中", "Ожидает", "En espera",
    ),
    "task.running": (
        "转换中", "Converting", "Converting",
        "Conversion", "変換中", "Конвертируется", "Convirtiendo",
    ),
    "task.paused": (
        "已暂停", "Paused", "Paused",
        "En pause", "一時停止", "Приостановлено", "En pausa",
    ),
    "task.completed": (
        "已完成", "Completed", "Completed",
        "Terminé", "完了", "Завершено", "Completado",
    ),
    "task.failed": (
        "失败", "Failed", "Failed",
        "Échoué", "失敗", "Сбой", "Fallido",
    ),
    "task.canceled": (
        "已取消", "Canceled", "Canceled",
        "Annulé", "キャンセル済み", "Отменено", "Cancelado",
    ),
    "task.skipped": (
        "已跳过", "Skipped", "Skipped",
        "Ignoré", "スキップ済み", "Пропущено", "Omitido",
    ),

    # ---------------------------------------------------- close.*
    "close.update_ready.title": (
        "更新已就绪，仍有转换任务进行中",
        "Update is ready, but conversions are still running",
        "Update is ready, but conversions are still running",
        "Mise à jour prête, mais des conversions sont en cours",
        "更新の準備が完了しましたが、変換タスクが進行中です",
        "Обновление готово, но задачи ещё выполняются",
        "Actualización lista, pero hay conversiones en curso",
    ),
    "close.update_ready.desc": (
        "FFmpeg 更新包已下载完成，将在退出程序后安装。\n"
        "你可以等待全部任务完成后自动安装，或立即退出"
        "（未完成任务会被取消，更新保留到下次退出时安装）。",
        "The FFmpeg update package has been downloaded and will install on exit.\n"
        "You can wait for all tasks to finish and install automatically, or exit now "
        "(incomplete tasks will be canceled; the update installs on next exit).",
        "The FFmpeg update package has been downloaded and will install on exit.\n"
        "You can wait for all tasks to finish and install automatically, or exit now "
        "(incomplete tasks will be canceled; the update installs on next exit).",
        "Le package de mise à jour FFmpeg est téléchargé et s'installera à la fermeture.\n"
        "Vous pouvez attendre la fin des tâches et l'installation automatique, ou quitter "
        "(les tâches incomplètes seront annulées ; l'installation se fera à la prochaine fermeture).",
        "FFmpeg 更新パッケージのダウンロードが完了しました。プログラム終了後にインストールされます。\n"
        "すべてのタスク完了後に自動インストールを待つか、今すぐ終了できます"
        "（未完了タスクはキャンセルされ、更新は次回終了時にインストールされます）。",
        "Пакет обновления FFmpeg скачан и установится при выходе.\n"
        "Можно дождаться завершения всех задач и автоустановки, либо выйти сейчас "
        "(незавершённые задачи будут отменены; обновление установится при следующем выходе).",
        "El paquete de actualización de FFmpeg se ha descargado y se instalará al salir.\n"
        "Puede esperar a que terminen todas las tareas para la instalación automática, o salir ahora "
        "(las tareas incompletas se cancelarán; la actualización se instalará en la próxima salida).",
    ),
    "close.update_ready.btn_return": (
        "返回继续使用", "Return to app", "Return to app",
        "Retourner à l'application", "アプリに戻る",
        "Вернуться в приложение", "Volver a la aplicación",
    ),
    "close.update_ready.btn_exit": (
        "立即退出（取消任务）", "Exit now (cancel tasks)",
        "Exit now (cancel tasks)",
        "Quitter maintenant (annuler les tâches)",
        "今すぐ終了（タスクをキャンセル）",
        "Выйти сейчас (отменить задачи)",
        "Salir ahora (cancelar tareas)",
    ),
    "close.update_ready.btn_wait": (
        "等待任务完成并安装", "Wait for tasks and install",
        "Wait for tasks and install",
        "Attendre la fin et installer",
        "タスク完了まで待ってインストール",
        "Дождаться задач и установить",
        "Esperar tareas e instalar",
    ),
    "close.preparing.title": (
        "正在准备退出", "Preparing to exit", "Preparing to exit",
        "Préparation de la fermeture", "終了を準備しています",
        "Подготовка к выходу", "Preparando salida",
    ),
    "close.preparing.caption": (
        "请稍候…", "Please wait…", "Please wait…",
        "Veuillez patienter…", "お待ちください…",
        "Подождите…", "Espere…",
    ),
    "close.downloading.caption": (
        "FFmpeg 更新包正在后台下载，等待下载完成后再退出（已下载内容会保留）…",
        "The FFmpeg update is downloading in the background. "
        "Waiting for download to finish before exiting (downloaded content is preserved)…",
        "The FFmpeg update is downloading in the background. "
        "Waiting for download to finish before exiting (downloaded content is preserved)…",
        "Téléchargement de la mise à jour FFmpeg en arrière-plan. "
        "En attente de la fin avant fermeture (le contenu téléchargé est conservé)…",
        "FFmpeg 更新パッケージをバックグラウンドでダウンロードしています。"
        "ダウンロード完了後に終了します（ダウンロード済み内容は保持されます）…",
        "Пакет обновления FFmpeg скачивается в фоновом режиме. "
        "Ожидание завершения загрузки перед выходом (скачанное сохраняется)…",
        "La actualización de FFmpeg se descarga en segundo plano. "
        "Esperando a que termine antes de salir (el contenido descargado se conserva)…",
    ),
    "close.waiting_tasks.title": (
        "等待转换任务完成", "Waiting for tasks to finish",
        "Waiting for tasks to finish",
        "En attente de la fin des tâches",
        "変換タスクの完了を待っています",
        "Ожидание завершения задач",
        "Esperando a que terminen las tareas",
    ),
    "close.waiting_tasks.caption": (
        "正在等待全部任务结束后退出并安装更新（转换中 {running} · 等待 {waiting}）…",
        "Waiting for all tasks to finish before exiting and installing the update "
        "(running {running} · waiting {waiting})…",
        "Waiting for all tasks to finish before exiting and installing the update "
        "(running {running} · waiting {waiting})…",
        "En attente de la fin de toutes les tâches avant fermeture et installation "
        "(en cours {running} · en attente {waiting})…",
        "すべてのタスク完了後に終了して更新をインストールします"
        "（変換中 {running} · 待機 {waiting}）…",
        "Ожидание завершения всех задач перед выходом и установкой обновления "
        "(выполняется {running} · ожидает {waiting})…",
        "Esperando a que terminen todas las tareas antes de salir e instalar "
        "(en curso {running} · en espera {waiting})…",
    ),
    "close.installing.title": (
        "正在安装 FFmpeg 更新", "Installing FFmpeg update",
        "Installing FFmpeg update",
        "Installation de la mise à jour FFmpeg",
        "FFmpeg 更新をインストールしています",
        "Установка обновления FFmpeg",
        "Instalando actualización de FFmpeg",
    ),
    "close.installing.caption": (
        "替换引擎文件并保留最近 1 个旧版本备份，完成后将自动退出…",
        "Replacing engine files and keeping the latest backup, "
        "the app will exit automatically when done…",
        "Replacing engine files and keeping the latest backup, "
        "the app will exit automatically when done…",
        "Remplacement des fichiers du moteur et conservation de la dernière sauvegarde ; "
        "fermeture automatique à la fin…",
        "エンジンファイルを置き換え、最新1件の旧バージョンバックアップを保持します。"
        "完了後に自動終了します…",
        "Замена файлов движка с сохранением последней резервной копии, "
        "после чего приложение автоматически закроется…",
        "Reemplazando archivos del motor y conservando la última copia de seguridad; "
        "la app se cerrará automáticamente al terminar…",
    ),
    "close.install_done.title": (
        "更新安装完成", "Update installed", "Update installed",
        "Mise à jour installée", "更新インストール完了",
        "Обновление установлено", "Actualización instalada",
    ),
    "close.install_done.caption": (
        "FFmpeg 已更新，感谢使用，再见。",
        "FFmpeg has been updated. Thank you for using the app. Goodbye.",
        "FFmpeg has been updated. Thank you for using the app. Goodbye.",
        "FFmpeg a été mis à jour. Merci d'avoir utilisé l'application. Au revoir.",
        "FFmpeg が更新されました。ご利用ありがとうございました。さようなら。",
        "FFmpeg обновлён. Спасибо за использование. До свидания.",
        "FFmpeg se ha actualizado. Gracias por usar la aplicación. Adiós.",
    ),
    "close.not_installed.title": (
        "本次未安装更新", "Update not installed this time",
        "Update not installed this time",
        "Mise à jour non installée cette fois",
        "今回の更新はインストールされませんでした",
        "Обновление не установлено в этот раз",
        "Actualización no instalada esta vez",
    ),
    "close.not_installed.caption": (
        "{message}；更新包已保留，将在下次退出时重试。",
        "{message}; the update package is preserved and will retry on next exit.",
        "{message}; the update package is preserved and will retry on next exit.",
        "{message} ; le package est conservé et sera réessayé à la prochaine fermeture.",
        "{message}；更新パッケージは保持され、次回終了時に再試行されます。",
        "{message}; пакет обновления сохранён и повторится при следующем выходе.",
        "{message}; el paquete se conserva y se reintentará en la próxima salida.",
    ),
    "close.confirm_exit.title": (
        "确认退出", "Confirm exit", "Confirm exit",
        "Confirmer la fermeture", "終了の確認",
        "Подтвердить выход", "Confirmar salida",
    ),
    "close.confirm_exit.desc": (
        "仍有转换任务正在进行，退出将取消所有未完成的任务。\n确定要退出吗？",
        "Conversion tasks are still running. Exiting will cancel all incomplete tasks.\n"
        "Are you sure you want to exit?",
        "Conversion tasks are still running. Exiting will cancel all incomplete tasks.\n"
        "Are you sure you want to exit?",
        "Des tâches de conversion sont en cours. Quitter annulera toutes les tâches incomplètes.\n"
        "Voulez-vous vraiment quitter ?",
        "変換タスクが進行中です。終了すると未完了のタスクがすべてキャンセルされます。\n本当に終了しますか？",
        "Задачи конвертации ещё выполняются. Выход отменит все незавершённые задачи.\n"
        "Вы уверены, что хотите выйти?",
        "Hay tareas de conversión en curso. Salir cancelará todas las tareas incompletas.\n"
        "¿Seguro que desea salir?",
    ),
    "close.confirm_exit.btn_exit": (
        "退出", "Exit", "Exit",
        "Quitter", "終了", "Выйти", "Salir",
    ),
    "close.confirm_exit.btn_continue": (
        "继续转换", "Keep converting", "Keep converting",
        "Continuer", "変換を続ける",
        "Продолжить", "Seguir convirtiendo",
    ),

    # ---------------------------------------------------- ffmpeg_install.*
    "ffmpeg_install.title": (
        "需要安装 FFmpeg 转换引擎",
        "FFmpeg conversion engine is required",
        "FFmpeg conversion engine is required",
        "Le moteur de conversion FFmpeg est requis",
        "FFmpeg 変換エンジンのインストールが必要です",
        "Требуется движок конвертации FFmpeg",
        "Se requiere el motor de conversión FFmpeg",
    ),
    "ffmpeg_install.desc": (
        "本程序依赖 FFmpeg 完成媒体转换。\n\n"
        "点击“是”立即自动下载并安装官方 FFmpeg 构建（约 80–100 MB，可随时在设置中重试）；\n"
        "你也可以稍后在“设置”页面手动操作。",
        "This app requires FFmpeg for media conversion.\n\n"
        "Click \"Yes\" to automatically download and install the official FFmpeg build "
        "(about 80–100 MB; retryable in Settings anytime);\n"
        "or do it manually later in the Settings page.",
        "This app requires FFmpeg for media conversion.\n\n"
        "Click \"Yes\" to automatically download and install the official FFmpeg build "
        "(about 80–100 MB; retryable in Settings anytime);\n"
        "or do it manually later in the Settings page.",
        "Ce programme nécessite FFmpeg pour la conversion.\n\n"
        "Cliquez « Oui » pour télécharger et installer automatiquement la version officielle "
        "(environ 80–100 Mo ; réessayable dans les Paramètres) ;\n"
        "ou faites-le manuellement plus tard dans les Paramètres.",
        "本プログラムはメディア変換に FFmpeg が必要です。\n\n"
        "「はい」をクリックすると公式 FFmpeg ビルドを自動ダウンロード・インストールします"
        "（約 80–100 MB、設定でいつでも再試行可能）。\n"
        "または後で「設定」ページから手動で操作することもできます。",
        "Для конвертации требуется FFmpeg.\n\n"
        "Нажмите «Да» для авто-скачивания и установки официальной сборки "
        "(около 80–100 МБ; можно повторить в «Настройках»);\n"
        "или сделайте это вручную позже в «Настройках».",
        "Esta app requiere FFmpeg para la conversión.\n\n"
        "Haga clic en «Sí» para descargar e instalar automáticamente la compilación oficial "
        "(unos 80–100 MB; se puede reintentar en Ajustes);\n"
        "o hágalo manualmente más tarde en Ajustes.",
    ),
    "ffmpeg_install.btn_download": (
        "立即下载", "Download now", "Download now",
        "Télécharger maintenant", "今すぐダウンロード",
        "Скачать сейчас", "Descargar ahora",
    ),
    "ffmpeg_install.btn_later": (
        "稍后", "Later", "Later",
        "Plus tard", "後で",
        "Позже", "Más tarde",
    ),

    # ---------------------------------------------------- error.*
    "error.unknown_encoder": (
        "当前 FFmpeg 版本不包含该编码器，请更新内置 FFmpeg",
        "The current FFmpeg version lacks this encoder; please update the bundled FFmpeg",
        "The current FFmpeg version lacks this encoder; please update the bundled FFmpeg",
        "La version actuelle de FFmpeg ne contient pas cet encodeur ; mettez à jour FFmpeg",
        "現在の FFmpeg バージョンにはこのエンコーダーが含まれていません。内蔵 FFmpegを更新してください",
        "Текущая версия FFmpeg не содержит этот энкодер; обновите встроенный FFmpeg",
        "La versión actual de FFmpeg no contiene este codificador; actualice el FFmpeg integrado",
    ),
    "error.corrupt": (
        "文件已损坏或不是有效的媒体文件",
        "The file is corrupt or not a valid media file",
        "The file is corrupt or not a valid media file",
        "Le fichier est corrompu ou n'est pas un fichier média valide",
        "ファイルが破損しているか、有効なメディアファイルではありません",
        "Файл повреждён или не является допустимым медиафайлом",
        "El archivo está dañado o no es un archivo multimedia válido",
    ),
    "error.permission": (
        "没有写入权限，请更换输出目录",
        "No write permission; please choose a different output directory",
        "No write permission; please choose a different output directory",
        "Pas de permission d'écriture ; choisissez un autre dossier de sortie",
        "書き込み権限がありません。別の出力ディレクトリを選択してください",
        "Нет прав на запись; выберите другую папку вывода",
        "Sin permiso de escritura; elija otro directorio de salida",
    ),
    "error.not_found": (
        "文件不存在或路径无效",
        "The file does not exist or the path is invalid",
        "The file does not exist or the path is invalid",
        "Le fichier n'existe pas ou le chemin est invalide",
        "ファイルが存在しないか、パスが無効です",
        "Файл не существует или путь недействителен",
        "El archivo no existe o la ruta no es válida",
    ),
    "error.exists": (
        "目标文件已存在",
        "The target file already exists",
        "The target file already exists",
        "Le fichier cible existe déjà",
        "出力ファイルはすでに存在します",
        "Целевой файл уже существует",
        "El archivo de destino ya existe",
    ),
    "error.codec": (
        "源文件编码不受支持，尝试更新 FFmpeg",
        "The source file encoding is not supported; try updating FFmpeg",
        "The source file encoding is not supported; try updating FFmpeg",
        "L'encodage du fichier source n'est pas pris en charge ; essayez de mettre à jour FFmpeg",
        "元ファイルのエンコードは対応していません。FFmpegの更新をお試しください",
        "Кодирование исходного файла не поддерживается; попробуйте обновить FFmpeg",
        "La codificación del archivo de origen no se admite; intente actualizar FFmpeg",
    ),
    "error.target_exists": (
        "目标已存在", "Target already exists",
        "Target already exists",
        "La cible existe déjà", "出力先はすでに存在します",
        "Цель уже существует", "El destino ya existe",
    ),
    "error.build_failed": (
        "未能构建转换命令",
        "Failed to build conversion command",
        "Failed to build conversion command",
        "Échec de la construction de la commande de conversion",
        "変換コマンドの構築に失敗しました",
        "Не удалось построить команду конвертации",
        "No se pudo construir el comando de conversión",
    ),
    "error.canceled": (
        "用户已取消转换", "Conversion canceled by user",
        "Conversion canceled by user",
        "Conversion annulée par l'utilisateur",
        "ユーザーによって変換がキャンセルされました",
        "Конвертация отменена пользователем",
        "Conversión cancelada por el usuario",
    ),
    "error.unknown": (
        "未知错误", "Unknown error", "Unknown error",
        "Erreur inconnue", "不明なエラー",
        "Неизвестная ошибка", "Error desconocido",
    ),
    "error.detail_suffix": (
        "\n（{detail}）", "\n({detail})", "\n({detail})",
        "\n({detail})", "\n（{detail}）", "\n({detail})", "\n({detail})",
    ),

    # ---------------------------------------------------- about_prism.*
    "about_prism.intro_title": (
        "软件简介", "Introduction", "Introduction",
        "Introduction", "ソフトウェア紹介",
        "О программе", "Introducción",
    ),
    "about_prism.intro_text": (
        "Prism（棱镜）是一款基于 FFmpeg 的现代 Fluent 风格媒体格式转换工具，"
        "支持音频、视频、图片三大类数十种主流格式的相互转换。"
        "界面简洁现代，支持批量处理与硬件加速，让媒体处理变得轻松高效。",
        "Prism is a modern Fluent-style media format converter powered by FFmpeg, "
        "supporting dozens of mainstream audio, video and image formats. "
        "Clean UI, batch processing and hardware acceleration make media handling easy.",
        "Prism is a modern Fluent-style media format converter powered by FFmpeg, "
        "supporting dozens of mainstream audio, video and image formats. "
        "Clean UI, batch processing and hardware acceleration make media handling easy.",
        "Prism est un convertisseur de formats multimédia moderne de style Fluent, "
        "propulsé par FFmpeg, prenant en charge des dizaines de formats audio, vidéo et image. "
        "Interface épurée, traitement par lots et accélération matérielle.",
        "Prism（プリズム）は FFmpeg をベースにした現代的 Fluent スタイルのメディア変換ツールです。"
        "音声・動画・画像の数十の主流フォーマットに対応。"
        "クリーンなUI、一括処理、ハードウェアアクセラレーションでメディア処理を手軽に。",
        "Prism — современный конвертер форматов медиа в стиле Fluent на базе FFmpeg, "
        "поддерживающий десятки аудио-, видео- и графических форматов. "
        "Пакетная обработка, аппаратное ускорение.",
        "Prism es un convertidor de formatos multimedia moderno de estilo Fluent, "
        "basado en FFmpeg, con decenas de formatos de audio, vídeo e imagen. "
        "Interfaz limpia, procesamiento por lotes y aceleración por hardware.",
    ),
    "about_prism.features_title": (
        "功能特点", "Features", "Features",
        "Fonctionnalités", "特徴", "Возможности", "Características",
    ),
    "about_prism.features_text": (
        "• 三大类支持：音频、视频、图片，覆盖数十种主流格式\n"
        "• 硬件加速：自动检测并启用 NVENC / QSV / AMF / Media Foundation\n"
        "• 批量队列：任务排队、暂停/恢复、自动并发调度\n"
        "• Fluent 风格：深色/浅色主题、强调色自定义、多语言界面\n"
        "• 内置 FFmpeg：自动下载、静默更新、版本管理",
        "• Three categories: audio, video, image with dozens of formats\n"
        "• Hardware acceleration: auto NVENC / QSV / AMF / Media Foundation\n"
        "• Batch queue: task scheduling, pause/resume, concurrency control\n"
        "• Fluent design: dark/light theme, accent color, multi-language\n"
        "• Bundled FFmpeg: auto download, silent updates, version management",
        "• Three categories: audio, video, image with dozens of formats\n"
        "• Hardware acceleration: auto NVENC / QSV / AMF / Media Foundation\n"
        "• Batch queue: task scheduling, pause/resume, concurrency control\n"
        "• Fluent design: dark/light theme, accent color, multi-language\n"
        "• Bundled FFmpeg: auto download, silent updates, version management",
        "• Trois catégories : audio, vidéo, image avec dizaines de formats\n"
        "• Accélération matérielle : NVENC / QSV / AMF / Media Foundation\n"
        "• File d'attente : planification, pause/reprise, concurrence\n"
        "• Style Fluent : thème sombre/clair, couleur d'accent, multi-langue\n"
        "• FFmpeg intégré : téléchargement auto, mises à jour silencieuses",
        "• 3カテゴリ対応：音声・動画・画像、数十の主要フォーマット\n"
        "• ハードウェアアクセラレーション：NVENC / QSV / AMF を自動検出\n"
        "• 一括キュー：タスク管理、一時停止/再開、同時実行制御\n"
        "• Fluentスタイル：暗/明テーマ、アクセントカラー、多言語\n"
        "• 内蔵FFmpeg：自動ダウンロード、サイレント更新",
        "• Три категории: аудио, видео, изображения — десятки форматов\n"
        "• Аппаратное ускорение: NVENC / QSV / AMF / Media Foundation\n"
        "• Очередь задач: планирование, пауза/возобновление, конкуренция\n"
        "• Стиль Fluent: темная/светлая тема, акцентный цвет, многоязычность\n"
        "• Встроенный FFmpeg: авто-загрузка, тихие обновления",
        "• Tres categorías: audio, vídeo, imagen con decenas de formatos\n"
        "• Aceleración por hardware: NVENC / QSV / AMF / Media Foundation\n"
        "• Cola de tareas: programación, pausa/reanudación, concurrencia\n"
        "• Diseño Fluent: tema oscuro/claro, color de acento, multiidioma\n"
        "• FFmpeg integrado: descarga automática, actualizaciones silenciosas",
    ),
    "about_prism.version_title": (
        "版本信息", "Version Info", "Version Info",
        "Informations de version", "バージョン情報",
        "Информация о версии", "Información de versión",
    ),
    "about_prism.version_current": (
        "当前版本", "Current version", "Current version",
        "Version actuelle", "現在のバージョン",
        "Текущая версия", "Versión actual",
    ),
    "about_prism.build_time": (
        "构建时间", "Build time", "Build time",
        "Heure de construction", "ビルド時間",
        "Время сборки", "Hora de compilación",
    ),
    "about_prism.license": (
        "开源协议", "License", "License",
        "Licence", "ライセンス", "Лицензия", "Licencia",
    ),
    "about_prism.dev_title": (
        "开发信息", "Developer Info", "Developer Info",
        "Informations de développement", "開発情報",
        "Информация о разработчике", "Información de desarrollador",
    ),
    "about_prism.author": (
        "作者", "Author", "Author",
        "Auteur", "作者", "Автор", "Autor",
    ),
    "about_prism.dev_years": (
        "开发年份", "Development years", "Development years",
        "Années de développement", "開発年数",
        "Годы разработки", "Años de desarrollo",
    ),
    "about_prism.history_title": (
        "版本历史", "Version History", "Version History",
        "Historique des versions", "バージョン履歴",
        "История версий", "Historial de versiones",
    ),
    "about_prism.history_text": (
        "v1.0.0 — 首次正式发布\n"
        "  · 支持音频 / 视频 / 图片三大类转换\n"
        "  · 硬件加速（NVENC / QSV / AMF / Media Foundation）\n"
        "  · Fluent 风格界面 + 深色 / 浅色主题 + 强调色跟随系统\n"
        "  · 多语言：简中、繁中（港/台）、英、法、日、俄、西\n"
        "  · 内置 FFmpeg 自动下载与静默更新\n"
        "  · 批量队列管理，支持暂停 / 恢复 / 取消 / 重试",
        "v1.0.0 — Initial public release\n"
        "  · Audio / video / image conversion\n"
        "  · Hardware acceleration (NVENC / QSV / AMF / Media Foundation)\n"
        "  · Fluent UI with dark/light theme and system accent color\n"
        "  · Multi-language: zh-CN, zh-HK, zh-TW, en, fr, ja, ru, es\n"
        "  · Bundled FFmpeg with auto-download and silent updates\n"
        "  · Batch queue with pause/resume/cancel/retry",
        "v1.0.0 — Initial public release\n"
        "  · Audio / video / image conversion\n"
        "  · Hardware acceleration (NVENC / QSV / AMF / Media Foundation)\n"
        "  · Fluent UI with dark/light theme and system accent color\n"
        "  · Multi-language: zh-CN, zh-HK, zh-TW, en, fr, ja, ru, es\n"
        "  · Bundled FFmpeg with auto-download and silent updates\n"
        "  · Batch queue with pause/resume/cancel/retry",
        "v1.0.0 — Première version publique\n"
        "  · Conversion audio / vidéo / image\n"
        "  · Accélération matérielle (NVENC / QSV / AMF / Media Foundation)\n"
        "  · UI Fluent avec thème sombre/clair et couleur d'accent système\n"
        "  · Multi-langue : zh-CN, zh-HK, zh-TW, en, fr, ja, ru, es\n"
        "  · FFmpeg intégré avec téléchargement auto et mises à jour\n"
        "  · File d'attente avec pause/reprise/annulation/reprise",
        "v1.0.0 — 初回公式リリース\n"
        "  · 音声 / 動画 / 画像変換\n"
        "  · ハードウェアアクセラレーション（NVENC / QSV / AMF / Media Foundation）\n"
        "  · Fluent UI、暗/明テーマ、システムアクセントカラー対応\n"
        "  · 多言語：簡中、繁中（港/台）、英、仏、日、露、西\n"
        "  · 内蔵FFmpeg自動ダウンロードとサイレント更新\n"
        "  · 一括キュー、一時停止/再開/キャンセル/リトライ",
        "v1.0.0 — Первая публичная версия\n"
        "  · Преобразование аудио / видео / изображений\n"
        "  · Аппаратное ускорение (NVENC / QSV / AMF / Media Foundation)\n"
        "  · Fluent UI с темной/светлой темой и системным акцентным цветом\n"
        "  · Многоязычность: zh-CN, zh-HK, zh-TW, en, fr, ja, ru, es\n"
        "  · Встроенный FFmpeg с авто-загрузкой и тихими обновлениями\n"
        "  · Очередь с паузой/возобновлением/отменой/повтором",
        "v1.0.0 — Primera versión pública\n"
        "  · Conversión de audio / vídeo / imagen\n"
        "  · Aceleración por hardware (NVENC / QSV / AMF / Media Foundation)\n"
        "  · UI Fluent con tema oscuro/claro y color de acento del sistema\n"
        "  · Multiidioma: zh-CN, zh-HK, zh-TW, en, fr, ja, ru, es\n"
        "  · FFmpeg integrado con descarga automática y actualizaciones\n"
        "  · Cola con pausa/reanudación/cancelación/reintento",
    ),
}


# ============================================================ I18nManager

class I18nManager(QObject):
    """全局多语言管理器：当前语言状态 + 切换信号。"""

    languageChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._current: str = DEFAULT_LANGUAGE
        self._detect_system_language()

    def set_language(self, code: str) -> None:
        """切换当前语言；不在 SUPPORTED_LANGUAGES 中时回退到默认。"""
        if code not in SUPPORTED_LANGUAGES:
            code = DEFAULT_LANGUAGE
        if code == self._current:
            return
        self._current = code
        self.languageChanged.emit(code)

    def current(self) -> str:
        return self._current

    def _detect_system_language(self) -> None:
        """启动时检测系统语言并设置当前语言。"""
        code = self._detect_system_locale()
        if code in SUPPORTED_LANGUAGES:
            self._current = code
        else:
            # 尝试匹配语言前缀（如 "fr-FR" → "fr"）
            prefix = code.split("-")[0].lower() if code else ""
            for lang in SUPPORTED_LANGUAGES:
                if lang.lower().startswith(prefix) and prefix:
                    self._current = lang
                    return
            self._current = DEFAULT_LANGUAGE

    @staticmethod
    def _detect_system_locale() -> str:
        """
        Windows 下使用 ctypes 调用 GetUserDefaultLocaleName；
        其他平台回退到 locale.getdefaultlocale()。
        """
        # Windows: 尝试通过 ctypes 获取用户默认区域
        if sys.platform == "win32":
            try:
                import ctypes

                # GetUserDefaultLocaleName 返回 BCP47 区域名称（如 "zh-CN"）
                buf = ctypes.create_unicode_buffer(85)
                # LOCALE_NAME_USER_DEFAULT = 0
                ret = ctypes.windll.kernel32.GetUserDefaultLocaleName(
                    buf, ctypes.sizeof(buf)
                )
                if ret > 0:
                    locale_name = buf.value
                    # 转换 "zh-CN" → "zh_CN" 以匹配 SUPPORTED_LANGUAGES
                    normalized = locale_name.replace("-", "_")
                    return normalized
            except Exception:
                pass

        # 回退：locale.getdefaultlocale()
        try:
            loc, _enc = locale.getdefaultlocale()
            if loc:
                return loc.replace("-", "_")
        except Exception:
            pass

        return DEFAULT_LANGUAGE


# 全局单例
i18n = I18nManager()


# ============================================================ 公共 API

def set_language(code: str) -> None:
    """设置当前界面语言。"""
    i18n.set_language(code)


def supported_languages() -> List[str]:
    """返回支持的语言代码列表。"""
    return list(SUPPORTED_LANGUAGES)


def _current_index() -> int:
    """获取当前语言在 _LANGS 中的索引（沿回退链查找）。"""
    code = i18n.current()
    # 沿回退链找到第一个在 _LANGS 中的代码
    seen = set()
    while code not in _LANGS and code not in seen:
        seen.add(code)
        code = _FALLBACKS.get(code, DEFAULT_LANGUAGE)
    try:
        return _LANGS.index(code)
    except ValueError:
        return _EN_INDEX


def t(key: str, **kwargs) -> str:
    """
    查找翻译文案。

    查找顺序：当前语言 → 英文 (en) → key 本身。
    支持 ``{placeholder}`` 插值。

    示例::

        t("convert.info.added.content", count=5)
        # → "已添加 5 个文件" / "Added 5 files" / ...
    """
    entry = _T.get(key)
    if entry is None:
        # 无此键，直接返回 key
        return key

    idx = _current_index()
    text = entry[idx] if idx < len(entry) else None

    # 回退到英文
    if not text:
        text = entry[_EN_INDEX] if _EN_INDEX < len(entry) else None

    # 仍然为空，返回 key
    if not text:
        return key

    # 插值
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text
