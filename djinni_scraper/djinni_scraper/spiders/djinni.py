import json
import os

import scrapy
import re

from scrapy.http import Response


class DjinniSpider(scrapy.Spider):
    name = "djinni"
    allowed_domains = ["djinni.co"]
    base_url = "https://djinni.co/jobs/?primary_keyword=Python"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config_path = os.path.join(os.path.dirname(__file__), "../technologies_config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
            self.technologies = config.get("technologies", [])

    def start_requests(self):
        for exp in range(11):
            url = f"{self.base_url}&exp_level={exp}y"
            yield scrapy.Request(url, callback=self.parse, meta={"exp_level": exp})

    def parse(self, response):
        jobs = response.css(".list-unstyled li")
        exp_level = response.meta["exp_level"]

        for job in jobs:
            link = response.urljoin(job.css(".job-item__title-link::attr(href)").get())
            if link:
                job_url = response.urljoin(link)
                self.logger.info(f"Job link: {job_url}")
                yield scrapy.Request(
                    job_url, callback=self.parce_job, meta={"exp_level": exp_level}
                )

    def parce_job(self, response: Response) -> dict:
        city = (
            response.css(
                'li.breadcrumb-item:nth-last-child(1) span[itemprop="name"]::text'
            )
            .get(default="N/A")
            .strip()
        )
        description = response.css(".job-post-description *::text").getall()
        description = " ".join([text.strip() for text in description])
        technologies_in_description = self.extract_technologies(
            description, self.technologies
        )
        exp_level = response.meta.get("exp_level", "N/A")
        english_level = response.xpath(
            "//strong[contains(text(), 'Upper-Intermediate') or contains(text(), 'Intermediate') or contains(text(), 'Advanced')]/text()"
        ).get()
        english_level = english_level.split("from")[-1].strip()

        job = {
            "title": response.css("div.row.mb-3 h1::text").get().strip(),
            "company": response.css(".job-details--title::text").get().strip(),
            "city": city if city != "Python" else "N/A",
            "description": description,
            "technologies": technologies_in_description,
            "experience_level": exp_level,
            "english_level": english_level,
        }
        return job

    @staticmethod
    def extract_technologies(description, tech_list):
        if description:
            found_technologies = [
                tech
                for tech in tech_list
                if re.search(
                    r"\b" + re.escape(tech) + r"\b", description, re.IGNORECASE
                )
            ]
            return ", ".join(found_technologies)
        return "NaN"
