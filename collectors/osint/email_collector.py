from collectors.base_collector import BaseCollector


class EmailCollector(BaseCollector):
    def collect(self, target):
        print(f"[EmailCollector] Collecting emails for {target}")
        return ["admin@" + target]
