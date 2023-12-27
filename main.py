import json
import sys
from typing import Any, Dict, List
from uagents import Agent, Bureau, Context, Model
from get_products import filter_by_ratings, get_cheapest_product, get_products


class Query(Model):
    name: str

class ProductsData(Model):
    products: List[Dict[str, Any]]
    
class BoughtProduct(Model):
    product_url: str


# Instantiate your agents
shopping_agent = Agent(name="shopping_agent")
product_agent = Agent(name="product_agent")
buying_agent = Agent(name="buying_agent")
filter_agent = Agent(name="filter_agent")


@shopping_agent.on_event("startup")
async def seting_up(ctx: Context):
    ctx.storage.set("completed", False)

@filter_agent.on_event("startup")
async def seting_up(ctx: Context):
    ctx.storage.set("products", "")


@product_agent.on_message(Query, replies={Query, ProductsData})
async def handle_message(ctx: Context, sender: str, msg: Query):
    print(f"Product query recieved from {sender}")
    # Send the product data back to the shopping agent
    products = get_products(msg.name)
    if len(products) > 0:
        await ctx.send(shopping_agent.address, Query(name="Products found!"))
        await ctx.send(filter_agent.address, ProductsData(products=products))
    else:
        ctx.logger.info(f"Sending no products back to {sender}")

@filter_agent.on_message(ProductsData)
async def handle_products_data(ctx: Context, sender: str, msg: ProductsData):
    ctx.logger.info(f"Products data received from {sender}")
    ctx.storage.set("products", json.dumps(msg.products))

# Define message handler for product_agent
@filter_agent.on_message(Query, replies={BoughtProduct})
async def handle_filter_query(ctx: Context, sender: str, msg: Query):
    ctx.logger.info(f"Filter query received from {sender}")
    products_json = ctx.storage.get("products")
    if products_json is not None:
        products = json.loads(products_json)
        print()
        filtered_products = filter_by_ratings(
            float(sys.argv[2] if sys.argv[2] else 0), products)
        # print(filtered_products)
        cheapest_product = get_cheapest_product(filtered_products)
        # print(cheapest_product)
        ctx.logger.info(f"Sending cheapest product back to {sender}")
        if (cheapest_product is not None):
            await ctx.send(shopping_agent.address, BoughtProduct(product_url=cheapest_product['product_title']+':::>>'+ cheapest_product['product_page_url']))

@buying_agent.on_message(Query,replies={Query})
async def handle_buying_data(ctx: Context, sender: str, msg: Query):
    await ctx.send(filter_agent.address, Query(name="Buy it!"))
    ctx.logger.info(f"Buying from data received from {sender}")
    ctx.logger.info(f"{msg.name}")


@shopping_agent.on_message(ProductsData, replies={Query})
async def handle_products_data(ctx: Context, sender: str, msg: ProductsData):
    ctx.logger.info(f"Products data received from {sender}")
    ctx.storage.set("products", json.dumps(msg.products))
    
@shopping_agent.on_message(BoughtProduct)
async def handle_bought_product(ctx: Context, sender: str, msg: BoughtProduct):
    ctx.logger.info(f"Bought product received from {sender}")
    get_bought_products_str = ctx.storage.get("bought_products") or ""
    get_bought_products = get_bought_products_str.split('|')
    get_bought_products.append(msg.product_url)
    ctx.storage.set("bought_products", '|'.join(get_bought_products))

@shopping_agent.on_message(Query)
async def handle_product_data(ctx: Context, sender: str, msg: Query):
    ctx.logger.info(f"Product data received from {sender}")
    await ctx.send(buying_agent.address,
                   Query(name="Thanks for shopping with us!"))
    ctx.storage.set("completed", True)


@shopping_agent.on_interval(period=5, messages=Query)
async def serve_the_user(ctx: Context):
    query = sys.argv[1] if len(sys.argv) > 1 else "levis"
    completed = ctx.storage.get("completed")
    ctx.logger.info(f"Querying for {query}")
    ctx.logger.info(f"Status: {completed}")
    if (not completed):
        await ctx.send(product_agent.address, Query(name=query))
    else:
        get_bought_products = ctx.storage.get("bought_products") or ""
        ctx.logger.info('\n'.join(get_bought_products.split('|')))


bureau = Bureau()
bureau.add(filter_agent)
bureau.add(buying_agent)
bureau.add(product_agent)
bureau.add(shopping_agent)

if __name__ == "__main__":
    bureau.run()
