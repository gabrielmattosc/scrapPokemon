import json
import scrapy


class PokemonScrapper(scrapy.Spider):
    name = "pokemonscrapper"
    domain = "https://pokemondb.net/"

    start_urls = ["https://pokemondb.net/pokedex/all"]

    def parse(self, response):
        with open("pokemons.json", "w+") as f:
            json.dump({}, f, indent=4, ensure_ascii=True, separators=(",", ": "))

        pokemons = response.css("#pokedex > tbody > tr")
        for pokemon in pokemons:
            link = pokemon.css("td.cell-name > a::attr(href)").get()
            yield response.follow(link, self.parse_pokemon)
            
    def parse_pokemon(self, response):
        pokemon_id = response.css(
            ".vitals-table > tbody > tr:nth-child(1) > td > strong::text"
        ).get()
        pokemon_name = response.css("#main > h1::text").get()
        url_pokemon = response.url

        # Coletar próximas evoluções
        evolutions = []
        current_evolution = response.css(
            "#main > div.infocard-list-evo > div:nth-child(3) > span.infocard-lg-data.text-muted > a::text"
        ).get()
        evolutions.append(current_evolution)
        if current_evolution:
            previous_evolution = response.css(
                "#main > div.infocard-list-evo > div:nth-child(1) > span.infocard-lg-data.text-muted > a::text"
            ).get()
            next_evolution = response.css(
                "#main > div.infocard-list-evo > div:nth-child(5) > span.infocard-lg-data.text-muted > a::text"
            ).get()
            if previous_evolution:
                evolutions.append(previous_evolution)
            if next_evolution:
                evolutions.append(next_evolution)

        # Coletar tamanho e peso
        size_weight_section = response.css(".vitals-table")
        size = size_weight_section.xpath(
            './/th[contains(text(), "Height")]/following-sibling::td/text()'
        ).get()
        size = float(size.split(" ")[0].replace("m", "").strip())
        size = str(size * 100) + " cm"
        weight = size_weight_section.xpath(
            './/th[contains(text(), "Weight")]/following-sibling::td/text()'
        ).get()
        weight = float(weight.split(" ")[0].replace("kg", "").strip())
        weight = str(weight) + " kg"

        # Coletar tipos do Pokémon
        types = response.css(".vitals-table .type-icon::text").getall()

        # Coletar habilidades
        abilities = []
        abilities_section = response.xpath(
            './/th[contains(text(), "Abilities")]/following-sibling::td'
        )
        for ability in abilities_section.css("span"):
            ability_name = ability.css("a::text").get()
            ability_url = self.domain + ability.css("a::attr(href)").get()
            ability_description = ability.css("a::attr(title)").get().strip()
            abilities.append(
                {
                    "name": ability_name,
                    "url": ability_url,
                    "description": ability_description,
                }
            )

        result = {
            pokemon_name: {
                "pokemon_id": pokemon_id,
                "pokemon_name": pokemon_name,
                "url": url_pokemon,
                "evolution": evolutions,
                "size": size,
                "weight": weight,
                "types": types,
                "abilities": abilities,
            }
        }

        try:
            with open("pokemons.json", "r+") as f:
                data = json.load(f)
                data.update(result)
                f.seek(0)
                json.dump(
                    dict(sorted(data.items(), key=lambda x: int(x[1]["pokemon_id"]))),
                    f,
                    indent=4,
                    ensure_ascii=True,
                    separators=(",", ": "),
                )
                f.truncate()
        except FileNotFoundError:
            with open("pokemons.json", "w") as f:
                json.dump(result, f, indent=4, ensure_ascii=True, separators=(",", ": "))

        yield result