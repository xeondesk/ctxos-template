from collectors.base_collector import BaseCollector

class SubdomainCollector(BaseCollector):
    def collect(self, target):
        print(f'[SubdomainCollector] Collecting subdomains for {target}')
        return ['sub1.' + target, 'sub2.' + target]
