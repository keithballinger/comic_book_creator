"""Command-line interface for Comic Book Creator."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.logging import RichHandler

from src.config import ConfigLoader
from src.processor.pipeline import ProcessingPipeline
from src.output import PageCompositor
from src.models import ProcessingOptions, StyleConfig
from src.cli_reference import reference

# Setup rich console
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="Comic Book Creator")
def cli():
    """Comic Book Creator - Transform scripts into illustrated comics using AI."""
    pass

# Add reference commands as a subgroup
cli.add_command(reference)


@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='output', help='Output directory')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.option('--style', '-s', type=click.Choice(['comic', 'manga', 'graphic_novel', 'cartoon']), 
              default='comic', help='Art style preset')
@click.option('--quality', '-q', type=click.Choice(['draft', 'standard', 'high']), 
              default='standard', help='Output quality')
@click.option('--pages', '-p', help='Page range (e.g., 1-3)')
@click.option('--parallel/--sequential', default=False, help='Parallel panel generation')
# Text rendering removed - Gemini handles all text
@click.option('--format', '-f', type=click.Choice(['png', 'pdf', 'cbz']), 
              multiple=True, default=['png'], help='Export formats')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def generate(script_path, output, config, style, quality, pages, parallel,
             format, verbose):
    """Generate a comic from a script file."""
    
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Display header
    console.print(Panel.fit(
        "[bold blue]Comic Book Creator[/bold blue]\n"
        "Transforming your script into visual art",
        border_style="blue"
    ))
    
    # Load configuration
    console.print("\n[yellow]Loading configuration...[/yellow]")
    try:
        config_loader = ConfigLoader(config_path=config) if config else ConfigLoader()
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load configuration: {e}")
        sys.exit(1)
    
    # Parse page range
    page_range = None
    if pages:
        try:
            parts = pages.split('-')
            if len(parts) == 2:
                page_range = (int(parts[0]), int(parts[1]))
            else:
                console.print(f"[red]Invalid page range format: {pages}[/red]")
                sys.exit(1)
        except ValueError:
            console.print(f"[red]Invalid page range: {pages}[/red]")
            sys.exit(1)
    
    # Create processing options
    options = ProcessingOptions(
        page_range=page_range,
        style_preset=style,
        quality=quality,
        parallel_generation=parallel,
        # Text rendering removed - Gemini handles all text
        export_formats=list(format)
    )
    
    # Display processing info
    info_table = Table(title="Processing Configuration", show_header=False)
    info_table.add_column("Setting", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Script", script_path)
    info_table.add_row("Output Directory", output)
    info_table.add_row("Style", style)
    info_table.add_row("Quality", quality)
    info_table.add_row("Pages", pages or "All")
    info_table.add_row("Generation Mode", "Parallel" if parallel else "Sequential")
    # Text rendering removed - Gemini handles all text
    info_table.add_row("Export Formats", ", ".join(format))
    
    console.print("\n", info_table, "\n")
    
    # Create pipeline
    console.print("[yellow]Initializing processing pipeline...[/yellow]")
    try:
        pipeline = ProcessingPipeline(
            config=config_loader,
            output_dir=output
        )
        console.print("[green]✓[/green] Pipeline initialized")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize pipeline: {e}")
        sys.exit(1)
    
    # Process script
    console.print("\n[yellow]Processing script...[/yellow]")
    try:
        # Run async processing
        result = asyncio.run(process_with_progress(pipeline, script_path, options))
        
        if result.success:
            console.print("\n[green]✓[/green] Comic generation completed successfully!")
            
            # Display summary
            summary_table = Table(title="Generation Summary")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")
            
            if result.generated_pages:
                summary_table.add_row("Pages Generated", str(len(result.generated_pages)))
                total_panels = sum(len(p.panels) for p in result.generated_pages)
                summary_table.add_row("Panels Generated", str(total_panels))
            
            summary_table.add_row("Processing Time", f"{result.processing_time:.2f} seconds")
            
            if result.metadata:
                if 'output_directory' in result.metadata:
                    summary_table.add_row("Output Location", result.metadata['output_directory'])
            
            console.print("\n", summary_table)
            
            # Save results
            console.print("\n[yellow]Saving results...[/yellow]")
            output_path = asyncio.run(pipeline.save_results(result))
            console.print(f"[green]✓[/green] Results saved to: {output_path}")
            
        else:
            console.print("\n[red]✗[/red] Comic generation failed!")
            if result.validation_result and result.validation_result.errors:
                console.print("\n[red]Validation Errors:[/red]")
                for error in result.validation_result.errors:
                    console.print(f"  • {error}")
            if result.metadata and 'error' in result.metadata:
                console.print(f"\n[red]Error:[/red] {result.metadata['error']}")
    
    except Exception as e:
        console.print(f"\n[red]✗[/red] Processing failed: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


async def process_with_progress(pipeline, script_path, options):
    """Process script with progress display."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        # Create main task
        main_task = progress.add_task("Processing script...", total=100)
        
        # Start processing
        result = await pipeline.process_script(script_path, options)
        
        # Update progress
        progress.update(main_task, completed=100)
        
        return result


@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
def validate(script_path):
    """Validate a comic script file."""
    console.print(Panel.fit(
        "[bold blue]Script Validator[/bold blue]",
        border_style="blue"
    ))
    
    console.print(f"\n[yellow]Validating script: {script_path}[/yellow]\n")
    
    try:
        from src.parser import ScriptParser, ScriptValidator
        
        # Parse script
        parser = ScriptParser()
        script = parser.parse_script(script_path)
        
        # Validate script
        validator = ScriptValidator()
        result = validator.validate_script(script)
        
        if result.is_valid:
            console.print("[green]✓[/green] Script is valid!")
            
            # Display script info
            info_table = Table(title="Script Information")
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="white")
            
            info_table.add_row("Title", script.title or "Untitled")
            info_table.add_row("Pages", str(len(script.pages)))
            total_panels = sum(len(page.panels) for page in script.pages)
            info_table.add_row("Total Panels", str(total_panels))
            
            # Count dialogue and effects
            total_dialogue = sum(
                len(panel.dialogue) 
                for page in script.pages 
                for panel in page.panels
            )
            total_captions = sum(
                len(panel.captions) 
                for page in script.pages 
                for panel in page.panels
            )
            total_sfx = sum(
                len(panel.sound_effects) 
                for page in script.pages 
                for panel in page.panels
            )
            
            info_table.add_row("Dialogue Lines", str(total_dialogue))
            info_table.add_row("Captions", str(total_captions))
            info_table.add_row("Sound Effects", str(total_sfx))
            
            console.print("\n", info_table)
            
            if result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  ⚠ {warning}")
        else:
            console.print("[red]✗[/red] Script validation failed!")
            console.print("\n[red]Errors:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
                
    except Exception as e:
        console.print(f"[red]✗[/red] Validation failed: {e}")
        sys.exit(1)


@cli.command()
def styles():
    """List available art styles."""
    console.print(Panel.fit(
        "[bold blue]Available Art Styles[/bold blue]",
        border_style="blue"
    ))
    
    styles_table = Table(title="Art Style Presets")
    styles_table.add_column("Style", style="cyan")
    styles_table.add_column("Description", style="white")
    
    styles_data = [
        ("comic", "Classic American comic book style"),
        ("manga", "Japanese manga art style"),
        ("graphic_novel", "Realistic graphic novel style"),
        ("cartoon", "Animated cartoon style"),
        ("noir", "Black and white noir style"),
        ("watercolor", "Soft watercolor painting style"),
        ("lineart", "Clean line art style"),
        ("digital", "Modern digital art style"),
    ]
    
    for style_name, description in styles_data:
        styles_table.add_row(style_name, description)
    
    console.print("\n", styles_table)
    console.print("\n[dim]Use --style option when generating to select a style[/dim]")


@cli.command()
def init():
    """Initialize a new comic project."""
    console.print(Panel.fit(
        "[bold blue]Comic Project Initializer[/bold blue]",
        border_style="blue"
    ))
    
    # Prompt for project details
    project_name = Prompt.ask("\n[cyan]Project name[/cyan]", default="my-comic")
    author = Prompt.ask("[cyan]Author name[/cyan]")
    style = Prompt.ask(
        "[cyan]Default art style[/cyan]",
        choices=["comic", "manga", "graphic_novel", "cartoon"],
        default="comic"
    )
    
    # Create project directory
    project_dir = Path(project_name)
    if project_dir.exists():
        if not Confirm.ask(f"[yellow]Directory '{project_name}' exists. Continue?[/yellow]"):
            console.print("[red]Project initialization cancelled[/red]")
            return
    else:
        project_dir.mkdir(parents=True)
    
    # Create default configuration
    config_content = f"""# Comic Book Creator Configuration
project:
  name: {project_name}
  author: {author}

generation:
  style: {style}
  quality: standard
  panel_width: 800
  panel_height: 600
  dpi: 300

api:
  rate_limit: 30

output:
  formats:
    - png
  directory: output
"""
    
    config_path = project_dir / "comic_config.yaml"
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    # Create sample script
    sample_script = """PAGE 1

PANEL 1
A wide establishing shot of a bustling city at dawn.
CAPTION: The city awakens...

PANEL 2
Close-up of our HERO looking determined.
HERO: Today's the day.

PANEL 3
Hero walks towards a towering building.
SFX: WHOOSH!

PAGE 2

PANEL 1
Interior of a high-tech laboratory.
CAPTION: Meanwhile, at the lab...

PANEL 2
The VILLAIN smirks while holding a device.
VILLAIN: Soon, it will all be mine!

PANEL 3
An alarm starts blaring.
SFX: BEEP! BEEP! BEEP!
"""
    
    script_path = project_dir / "sample_script.txt"
    with open(script_path, 'w') as f:
        f.write(sample_script)
    
    # Create directories
    (project_dir / "scripts").mkdir(exist_ok=True)
    (project_dir / "output").mkdir(exist_ok=True)
    (project_dir / "resources").mkdir(exist_ok=True)
    
    # Display success message
    console.print(f"\n[green]✓[/green] Project '{project_name}' initialized successfully!")
    
    success_table = Table(show_header=False)
    success_table.add_column("Item", style="cyan")
    success_table.add_column("Path", style="white")
    
    success_table.add_row("Configuration", str(config_path))
    success_table.add_row("Sample Script", str(script_path))
    success_table.add_row("Scripts Directory", str(project_dir / "scripts"))
    success_table.add_row("Output Directory", str(project_dir / "output"))
    
    console.print("\n", success_table)
    console.print("\n[dim]To generate the sample comic, run:[/dim]")
    console.print(f"  comic-creator generate {script_path}")


@cli.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed statistics')
def stats(detailed):
    """Display generation statistics."""
    console.print(Panel.fit(
        "[bold blue]Generation Statistics[/bold blue]",
        border_style="blue"
    ))
    
    # This would normally load from a stats file or database
    console.print("\n[yellow]Feature coming soon![/yellow]")
    console.print("[dim]Statistics tracking will be available in the next version[/dim]")


if __name__ == '__main__':
    cli()