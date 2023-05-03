import typer
import g2

app = typer.Typer()

@app.command()
def hello():
    print("hello")

@app.command()
def fetch_categories():
    g2.fetch_and_save_categories()

@app.command()
def fetch_item_links():
    g2.get_item_links_from_categories_and_save()

@app.command()
def fetch_items():
    g2.fetch_links_and_save_as_items()

@app.command()
def fetch_item_prices():
    g2.fetch_item_prices_and_save()

if __name__ == "__main__":
    app()