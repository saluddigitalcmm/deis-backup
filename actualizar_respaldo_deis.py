from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime
import shutil
import subprocess
import sys


# ============================================================
# CONFIGURACIÓN
# ============================================================

YEAR = 2026

FILE_NAME = f"AtencionesUrgencia{YEAR}.zip"

DEIS_URL = (
    "https://repositoriodeis.minsal.cl/"
    f"SistemaAtencionesUrgencia/{FILE_NAME}"
)

REPO_DIR = Path(
    r"C:\Users\sbaez\Documents\Proyectos\Fondef-IRA\Github\deis-backup"
)

DRIVE_DIR = Path(
    r"G:\Mi unidad\Plataforma Fondef\deis-backup"
)

DOWNLOADS_DIR = REPO_DIR / "downloads"
LOGS_DIR = REPO_DIR / "logs"

TEMP_FILE = DOWNLOADS_DIR / FILE_NAME
REPO_FILE = REPO_DIR / FILE_NAME
DRIVE_FILE = DRIVE_DIR / FILE_NAME

UPDATE_INFO_FILE = REPO_DIR / "ultima_actualizacion.txt"
LOG_FILE = LOGS_DIR / "actualizar_respaldo_deis.log"

GIT_BRANCH = "main"


# ============================================================
# UTILIDADES
# ============================================================

def log(message: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def file_size(path: Path) -> int | None:
    if not path.exists():
        return None

    return path.stat().st_size


def run_command(
    command: list[str],
    cwd: Path
) -> subprocess.CompletedProcess:

    log(f"Ejecutando comando: {' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=False,
    )

    if result.stdout.strip():
        log("STDOUT:")
        log(result.stdout.strip())

    if result.stderr.strip():
        log("STDERR:")
        log(result.stderr.strip())

    if result.returncode != 0:
        raise RuntimeError(
            f"El comando falló con código {result.returncode}: "
            f"{' '.join(command)}"
        )

    return result


# ============================================================
# DESCARGA DESDE DEIS
# ============================================================

def download_from_deis() -> None:

    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    log(f"Descargando archivo desde DEIS: {DEIS_URL}")

    request = Request(
        DEIS_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        },
    )

    try:

        with urlopen(request, timeout=900) as response:

            with TEMP_FILE.open("wb") as out_file:

                shutil.copyfileobj(
                    response,
                    out_file
                )

    except HTTPError as e:

        raise RuntimeError(
            f"Error HTTP descargando desde DEIS: "
            f"{e.code} {e.reason}"
        ) from e

    except URLError as e:

        raise RuntimeError(
            f"Error de conexión descargando desde DEIS: {e}"
        ) from e

    except TimeoutError as e:

        raise RuntimeError(
            "Timeout descargando desde DEIS"
        ) from e

    if (
        not TEMP_FILE.exists()
        or TEMP_FILE.stat().st_size == 0
    ):
        raise RuntimeError(
            "La descarga terminó, pero el archivo "
            "está vacío o no existe."
        )

    log(
        f"Descarga completada: {TEMP_FILE}"
    )

    log(
        f"Tamaño descargado: "
        f"{TEMP_FILE.stat().st_size} bytes"
    )


# ============================================================
# ACTUALIZACIÓN DEL ARCHIVO EN EL REPOSITORIO
# ============================================================

def update_repo_file() -> None:

    log(
        f"Actualizando archivo en repo: {REPO_FILE}"
    )

    shutil.copy2(
        TEMP_FILE,
        REPO_FILE
    )


# ============================================================
# RESPALDO OPCIONAL EN GOOGLE DRIVE
# ============================================================

def update_drive_file() -> bool:
    """
    Intenta actualizar el respaldo en Google Drive.

    Retorna:
        True  -> si se actualizó correctamente.
        False -> si Google Drive no está disponible.

    La ausencia de Google Drive NO detiene el proceso.
    """

    if not DRIVE_DIR.exists():

        log(
            f"AVISO: Google Drive no está disponible: "
            f"{DRIVE_DIR}"
        )

        log(
            "Se omite el respaldo en Google Drive "
            "y se continúa con GitHub."
        )

        return False

    try:

        log(
            f"Actualizando archivo en Google Drive: "
            f"{DRIVE_FILE}"
        )

        shutil.copy2(
            TEMP_FILE,
            DRIVE_FILE
        )

        log(
            "Respaldo en Google Drive actualizado correctamente."
        )

        return True

    except Exception as e:

        log(
            f"AVISO: No fue posible actualizar Google Drive: {e}"
        )

        log(
            "El proceso continuará únicamente con el respaldo en GitHub."
        )

        return False


# ============================================================
# ARCHIVO DE INFORMACIÓN DE ACTUALIZACIÓN
# ============================================================

def update_info_file(
    new_size: int,
    drive_updated: bool
) -> None:

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    if drive_updated:

        drive_status = (
            f"Actualizado correctamente - {DRIVE_DIR}"
        )

    else:

        drive_status = (
            "No disponible / respaldo omitido"
        )

    content = (
        f"Fecha: {now}\n"
        f"Archivo: {FILE_NAME}\n"
        f"Año: {YEAR}\n"
        f"Tamaño: {new_size} bytes\n"
        f"Origen: DEIS\n"
        f"URL origen: {DEIS_URL}\n"
        f"Respaldo GitHub: saluddigitalcmm/deis-backup\n"
        f"Respaldo Google Drive: {drive_status}\n"
    )

    log(
        f"Actualizando archivo de estado: "
        f"{UPDATE_INFO_FILE}"
    )

    UPDATE_INFO_FILE.write_text(
        content,
        encoding="utf-8"
    )


# ============================================================
# OPERACIONES GIT
# ============================================================

def git_has_changes() -> bool:

    result = subprocess.run(
        [
            "git",
            "status",
            "--porcelain"
        ],
        cwd=str(REPO_DIR),
        text=True,
        capture_output=True,
        shell=False,
    )

    if result.returncode != 0:

        raise RuntimeError(
            "No se pudo revisar el estado de Git."
        )

    return bool(
        result.stdout.strip()
    )


def update_git() -> None:

    if not git_has_changes():

        log(
            "Git no detectó cambios. "
            "No se hará commit."
        )

        return

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    commit_message = (
        f"Actualizar respaldo DEIS "
        f"{YEAR} - {today}"
    )

    run_command(
        [
            "git",
            "add",
            FILE_NAME,
            "ultima_actualizacion.txt",
            "README.md",
            ".gitignore",
        ],
        REPO_DIR
    )

    run_command(
        [
            "git",
            "commit",
            "-m",
            commit_message,
        ],
        REPO_DIR
    )

    run_command(
        [
            "git",
            "push",
            "origin",
            GIT_BRANCH,
        ],
        REPO_DIR
    )

    log(
        "Cambios enviados correctamente a GitHub."
    )


# ============================================================
# FLUJO PRINCIPAL
# ============================================================

def main() -> int:

    log("=" * 70)

    log(
        "Inicio del proceso de actualización "
        "del respaldo DEIS"
    )

    try:

        # ----------------------------------------------------
        # Validar repositorio local
        # ----------------------------------------------------

        if not REPO_DIR.exists():

            raise RuntimeError(
                f"No existe REPO_DIR: {REPO_DIR}"
            )

        # ----------------------------------------------------
        # Google Drive es OPCIONAL
        # ----------------------------------------------------

        if not DRIVE_DIR.exists():

            log(
                f"AVISO: No existe DRIVE_DIR: "
                f"{DRIVE_DIR}"
            )

            log(
                "Google Drive no está disponible. "
                "El proceso continuará normalmente "
                "con el respaldo en GitHub."
            )

        # ----------------------------------------------------
        # Descargar archivo DEIS
        # ----------------------------------------------------

        download_from_deis()

        new_size = file_size(
            TEMP_FILE
        )

        old_size = file_size(
            REPO_FILE
        )

        log(
            f"Tamaño actual en repo: "
            f"{old_size} bytes"
        )

        log(
            f"Tamaño nuevo descargado: "
            f"{new_size} bytes"
        )

        # ----------------------------------------------------
        # Comparar archivo nuevo vs existente
        # ----------------------------------------------------

        if (
            old_size is not None
            and new_size == old_size
        ):

            log(
                "El tamaño del archivo no cambió."
            )

            log(
                "No se actualiza Git ni Google Drive."
            )

            log(
                "Fin del proceso sin cambios."
            )

            return 0

        log(
            "El archivo cambió o no existía previamente."
        )

        log(
            "Actualizando respaldos."
        )

        # ----------------------------------------------------
        # Actualizar repo local
        # ----------------------------------------------------

        update_repo_file()

        # ----------------------------------------------------
        # Google Drive: intentar, pero NO detener si falla
        # ----------------------------------------------------

        drive_updated = update_drive_file()

        # ----------------------------------------------------
        # Actualizar información
        # ----------------------------------------------------

        update_info_file(
            new_size,
            drive_updated
        )

        # ----------------------------------------------------
        # Git commit + push
        # ----------------------------------------------------

        update_git()

        log(
            "Proceso finalizado correctamente."
        )

        return 0

    except Exception as e:

        log(
            f"ERROR: {e}"
        )

        return 1


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    sys.exit(main())