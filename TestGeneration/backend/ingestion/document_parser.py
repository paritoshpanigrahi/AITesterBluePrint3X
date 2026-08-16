import os


class DocumentParser:
    def parse(self, filepath):
        if not filepath or not os.path.isfile(filepath):
            return ""

        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext in (".txt", ".md"):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()

            elif ext == ".pdf":
                return self._parse_pdf(filepath)

            elif ext == ".docx":
                return self._parse_docx(filepath)

            elif ext in (".xlsx", ".xls"):
                return self._parse_xlsx(filepath)

            elif ext == ".csv":
                return self._parse_csv(filepath)

            elif ext in (".json", ".yaml", ".yml"):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
        except Exception:
            pass

        return ""

    def _parse_pdf(self, filepath):
        try:
            import subprocess
            result = subprocess.run(
                ["pdftotext", filepath, "-"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout[:5000]
        except Exception:
            pass
        return ""

    def _parse_docx(self, filepath):
        try:
            from docx import Document
            doc = Document(filepath)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)[:5000]
        except Exception:
            return ""

    def _parse_xlsx(self, filepath):
        try:
            import pandas as pd
            dfs = pd.read_excel(filepath, sheet_name=None)
            texts = []
            for sheet_name, df in dfs.items():
                texts.append(f"--- Sheet: {sheet_name} ---")
                texts.append(df.to_string(index=False))
            return "\n".join(texts)[:5000]
        except Exception:
            return ""

    def _parse_csv(self, filepath):
        try:
            import pandas as pd
            df = pd.read_csv(filepath)
            return df.to_string(index=False)[:5000]
        except Exception:
            return ""
