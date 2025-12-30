"""Interfaz de línea de comandos usando Rich."""

import asyncio
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.api_clients import APIManager, GameDeal
from src.database import Database
from src.watchlist import WatchlistManager
from src.deal_analyzer import DealAnalyzer
from src.notifier import Notifier


console = Console()


class CLI:
    """Interfaz de línea de comandos."""
    
    def __init__(self):
        self.db = Database()
        self.api_manager = APIManager()
        self.watchlist_manager = WatchlistManager(self.db, self.api_manager)
        self.analyzer = DealAnalyzer(self.db)
        self.notifier = Notifier()
    
    def display_deals_table(self, deals: List[GameDeal], title: str = "Ofertas Encontradas"):
        """Muestra una tabla de ofertas."""
        if not deals:
            console.print("[yellow]No se encontraron ofertas.[/yellow]")
            return
        
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Juego", style="cyan", no_wrap=True)
        table.add_column("Tienda", style="green")
        table.add_column("Precio", justify="right", style="yellow")
        table.add_column("Original", justify="right", style="dim")
        table.add_column("Descuento", justify="right", style="bold red")
        table.add_column("URL", style="blue")
        
        for deal in deals:
            discount_text = f"{deal.discount_percent:.1f}%"
            if deal.discount_percent >= 75:
                discount_text = f"[bold red]{discount_text}[/bold red]"
            
            table.add_row(
                deal.title[:50],  # Limitar longitud
                deal.store,
                f"${deal.price:.2f}",
                f"${deal.original_price:.2f}" if deal.original_price > deal.price else "-",
                discount_text,
                deal.url[:60]  # Limitar longitud
            )
        
        console.print(table)
    
    def display_watchlist(self):
        """Muestra la watchlist actual."""
        watchlist = self.watchlist_manager.get_games()
        
        if not watchlist:
            console.print("[yellow]La watchlist está vacía.[/yellow]")
            return
        
        table = Table(title="Watchlist", show_header=True, header_style="bold cyan")
        table.add_column("Juego", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Precio Objetivo", justify="right", style="yellow")
        table.add_column("Tienda", style="green")
        table.add_column("Última Verificación", style="dim")
        
        for item in watchlist:
            target_price = f"${item['target_price']:.2f}" if item.get('target_price') else "N/A"
            last_checked = item.get('last_checked', 'Nunca') or 'Nunca'
            
            table.add_row(
                item['game_title'],
                item.get('game_id', 'N/A') or 'N/A',
                target_price,
                item.get('store', 'Cualquiera') or 'Cualquiera',
                str(last_checked)
            )
        
        console.print(table)
    
    def display_amazing_deals(self):
        """Muestra ofertas imperdibles guardadas."""
        deals = self.db.get_amazing_deals(limit=20)
        
        if not deals:
            console.print("[yellow]No hay ofertas imperdibles guardadas.[/yellow]")
            return
        
        table = Table(title="Ofertas Imperdibles", show_header=True, header_style="bold red")
        table.add_column("Juego", style="cyan")
        table.add_column("Tienda", style="green")
        table.add_column("Precio", justify="right", style="yellow")
        table.add_column("Descuento", justify="right", style="bold red")
        table.add_column("Razón", style="magenta")
        table.add_column("Fecha", style="dim")
        
        for deal in deals:
            table.add_row(
                deal['game_title'],
                deal['store'],
                f"${deal['price']:.2f}",
                f"{deal['discount_percent']:.1f}%",
                deal['reason'],
                str(deal['timestamp'])
            )
        
        console.print(table)
    
    async def search_game(self, query: str):
        """Busca un juego en todas las plataformas."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Buscando '{query}'...", total=None)
            deals = await self.api_manager.search_game_global(query)
            progress.update(task, completed=True)
        
        if deals:
            self.display_deals_table(deals, f"Resultados para: {query}")
            
            # Analizar ofertas imperdibles
            amazing_deals = []
            for deal in deals:
                is_amazing, reason = self.analyzer.is_amazing_deal(deal)
                if is_amazing:
                    amazing_deals.append((deal, reason))
            
            if amazing_deals:
                console.print("\n[bold red]🔥 OFERTAS IMPERDIBLES ENCONTRADAS:[/bold red]")
                for deal, reason in amazing_deals:
                    console.print(Panel(
                        f"[cyan]{deal.title}[/cyan]\n"
                        f"Tienda: [green]{deal.store}[/green]\n"
                        f"Precio: [yellow]${deal.price:.2f}[/yellow]\n"
                        f"Descuento: [bold red]{deal.discount_percent:.1f}%[/bold red]\n"
                        f"Razón: [magenta]{reason}[/magenta]\n"
                        f"[blue]{deal.url}[/blue]",
                        title="🔥 Oferta Imperdible",
                        border_style="red"
                    ))
        else:
            console.print(f"[red]No se encontraron resultados para '{query}'[/red]")
    
    async def add_to_watchlist(self):
        """Agrega un juego a la watchlist."""
        game_title = Prompt.ask("Nombre del juego")
        game_id = Prompt.ask("ID del juego (opcional, presiona Enter para omitir)", default="")
        target_price = Prompt.ask("Precio objetivo (opcional, presiona Enter para omitir)", default="")
        store = Prompt.ask("Tienda específica (opcional, presiona Enter para omitir)", default="")
        
        target_price_float = float(target_price) if target_price else None
        game_id = game_id if game_id else None
        store = store if store else None
        
        if self.watchlist_manager.add_game(game_title, game_id, target_price_float, store):
            console.print(f"[green]✓[/green] '{game_title}' agregado a la watchlist")
        else:
            console.print(f"[red]✗[/red] Error al agregar '{game_title}' a la watchlist")
    
    async def check_watchlist(self):
        """Verifica todos los juegos en la watchlist."""
        watchlist = self.watchlist_manager.get_games()
        
        if not watchlist:
            console.print("[yellow]La watchlist está vacía.[/yellow]")
            return
        
        console.print(f"[cyan]Verificando {len(watchlist)} juego(s) en la watchlist...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Verificando precios...", total=None)
            results = await self.watchlist_manager.check_all_games()
            progress.update(task, completed=True)
        
        if results:
            # Separar ofertas normales, imperdibles y que cumplen precio objetivo
            normal_deals = []
            amazing_deals = []
            target_deals = []
            
            for result in results:
                deal = result["deal"]
                if result["is_amazing_deal"]:
                    amazing_deals.append((deal, result["analysis"]["reason"]))
                elif result["meets_target"]:
                    target_deals.append(deal)
                else:
                    normal_deals.append(deal)
            
            # Mostrar ofertas imperdibles
            if amazing_deals:
                console.print("\n[bold red]🔥 OFERTAS IMPERDIBLES:[/bold red]")
                for deal, reason in amazing_deals:
                    console.print(Panel(
                        f"[cyan]{deal.title}[/cyan]\n"
                        f"Tienda: [green]{deal.store}[/green]\n"
                        f"Precio: [yellow]${deal.price:.2f}[/yellow]\n"
                        f"Descuento: [bold red]{deal.discount_percent:.1f}%[/bold red]\n"
                        f"Razón: [magenta]{reason}[/magenta]\n"
                        f"[blue]{deal.url}[/blue]",
                        title="🔥 Oferta Imperdible",
                        border_style="red"
                    ))
            
            # Mostrar ofertas que cumplen precio objetivo
            if target_deals:
                console.print("\n[bold yellow]🎯 PRECIOS OBJETIVO ALCANZADOS:[/bold yellow]")
                self.display_deals_table(target_deals, "Precios Objetivo")
            
            # Mostrar otras ofertas
            if normal_deals:
                console.print("\n[bold cyan]📊 OTRAS OFERTAS:[/bold cyan]")
                self.display_deals_table(normal_deals, "Ofertas Encontradas")
        else:
            console.print("[yellow]No se encontraron ofertas para los juegos en la watchlist.[/yellow]")
    
    def show_menu(self):
        """Muestra el menú principal."""
        console.print(Panel.fit(
            "[bold cyan]Game Deal Hunter[/bold cyan]\n"
            "Monitorea ofertas de juegos en múltiples plataformas",
            title="🎮",
            border_style="cyan"
        ))
        
        console.print("\n[bold]Opciones:[/bold]")
        console.print("1. Buscar juego")
        console.print("2. Ver watchlist")
        console.print("3. Agregar a watchlist")
        console.print("4. Eliminar de watchlist")
        console.print("5. Verificar watchlist")
        console.print("6. Ver ofertas imperdibles")
        console.print("7. Salir")
    
    async def run(self):
        """Ejecuta la CLI."""
        while True:
            self.show_menu()
            choice = Prompt.ask("\n[bold cyan]Selecciona una opción[/bold cyan]", choices=["1", "2", "3", "4", "5", "6", "7"])
            
            if choice == "1":
                query = Prompt.ask("Nombre del juego a buscar")
                await self.search_game(query)
            
            elif choice == "2":
                self.display_watchlist()
            
            elif choice == "3":
                await self.add_to_watchlist()
            
            elif choice == "4":
                game_title = Prompt.ask("Nombre del juego a eliminar")
                store = Prompt.ask("Tienda (opcional, presiona Enter para omitir)", default="")
                store = store if store else None
                
                if self.watchlist_manager.remove_game(game_title, store):
                    console.print(f"[green]✓[/green] '{game_title}' eliminado de la watchlist")
                else:
                    console.print(f"[red]✗[/red] Error al eliminar '{game_title}'")
            
            elif choice == "5":
                await self.check_watchlist()
            
            elif choice == "6":
                self.display_amazing_deals()
            
            elif choice == "7":
                console.print("[yellow]¡Hasta luego![/yellow]")
                break
            
            console.print()  # Línea en blanco

