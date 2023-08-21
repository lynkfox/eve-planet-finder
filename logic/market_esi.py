from bravado.client import SwaggerClient

client = SwaggerClient.from_url("https://esi.evetech.net/latest/swagger.json")

prices = client.Market.get_markets_region_id_orders(region_id=10000032, order_type="all").response().result

print(prices)
