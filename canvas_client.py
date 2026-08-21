"""
Cliente central para comunicação com a API do Canvas.
"""

import time
import requests
import urllib3

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

from config import (
    MAX_RATE_LIMIT_RETRIES,
    RATE_LIMIT_RETRY_SECONDS,
    REQUEST_DELAY,
    TOKEN,
    VERIFY_SSL,
    CANVAS_API_URL,
    RED,
    YELLOW,
    RESET
)


class CanvasClient:
    def __init__(self):
        self.base_url = CANVAS_API_URL
        self.session = self._create_session()

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json+canvas-string-ids, application/json",
            "Authorization": TOKEN
        }

    # ======================================================
    # SESSION
    # ======================================================

    def _create_session(
        self,
        retries=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    ):
        session = requests.Session()

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist
        )

        adapter = HTTPAdapter(max_retries=retry)

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    # ======================================================
    # REQUEST HELPERS
    # ======================================================

    def _build_url(self, endpoint):
        if endpoint.startswith("http"):
            return endpoint

        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def get(self, endpoint, **kwargs):
        time.sleep(REQUEST_DELAY)
        return self.session.get(
            self._build_url(endpoint),
            headers=self.headers,
            verify=VERIFY_SSL,
            **kwargs
        )

    def post(self, endpoint, **kwargs):
        time.sleep(REQUEST_DELAY)
        return self.session.post(
            self._build_url(endpoint),
            headers=self.headers,
            verify=VERIFY_SSL,
            **kwargs
        )

    def put(self, endpoint, **kwargs):
        time.sleep(REQUEST_DELAY)
        return self.session.put(
            self._build_url(endpoint),
            headers=self.headers,
            verify=VERIFY_SSL,
            **kwargs
        )

    def delete(self, endpoint, **kwargs):
        time.sleep(REQUEST_DELAY)
        return self.session.delete(
            self._build_url(endpoint),
            headers=self.headers,
            verify=VERIFY_SSL,
            **kwargs
        )

    # ======================================================
    # COURSES
    # ======================================================

    def get_course_id(self, identifier):
        """
        Busca um curso pelo course_code.
        """

        try:
            response = self.get(
                "/accounts/self/courses",
                params={
                    "search_term": identifier
                }
            )

            response.raise_for_status()

            matches = [
                course
                for course in response.json()
                if str(identifier).strip().upper()
                in str(course.get("course_code", "")).upper()
            ]

            if not matches:
                return None

            return matches[0]["id"]

        except Exception as exc:
            print(
                f"{RED}Erro ao localizar curso "
                f"{identifier}: {exc}{RESET}"
            )
            return None

    # ======================================================
    # MIGRATIONS
    # ======================================================

    def wait_for_migration_state(
        self,
        migration_url,
        target_state,
        timeout=300
    ):
        """
        Aguarda a migração atingir o estado informado.
        """

        start_time = time.time()

        while (time.time() - start_time) < timeout:

            response = self.get(migration_url)

            if response.status_code == 200:

                state = response.json().get(
                    "workflow_state"
                )

                if state == target_state:
                    return True

                if state == "failed":
                    return False

                print(
                    f"      Estado atual: {state}",
                    end="\r"
                )

            time.sleep(2)

        print(
            f"{YELLOW}Timeout aguardando migração.{RESET}"
        )

        return False

    def has_running_migrations(self, course_id):
        """
        Verifica se existem migrações em andamento.
        """

        response = self.get(
            f"/courses/{course_id}/content_migrations"
        )

        if response.status_code != 200:
            return False

        migrations = response.json()

        return any(
            migration.get("workflow_state")
            in ["queued", "running", "started"]
            for migration in migrations
        )
    def _handle_rate_limit(
        self,
        response,
        retry_count=0
        ):
        """
        Trata respostas 429.
        """

        if response.status_code != 429:
            return False

        if retry_count >= MAX_RATE_LIMIT_RETRIES:
            raise Exception(
                "Máximo de tentativas por Rate Limit atingido."
            )

        print(
            f"\n[RATE LIMIT] "
            f"Aguardando {RATE_LIMIT_RETRY_SECONDS}s..."
        )

        time.sleep(RATE_LIMIT_RETRY_SECONDS)

        return True