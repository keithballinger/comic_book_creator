"""CLI command for reference experiments."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
import logging

from src.refexp import (
    RefExpParser,
    CombinationGenerator,
    RefExpImageGenerator,
    ReferenceTracker,
    ExperimentSession
)
from src.api.gemini_client import GeminiClient
from src.config import ConfigLoader

# Setup console
console = Console()
logger = logging.getLogger(__name__)


@click.command(name='ref-exp')
@click.argument('yaml_file', type=click.Path(exists=True))
@click.option('--iterations', default='10', help='Number of combinations or "all"')
@click.option('--output', '-o', default='output/reference_experiments', help='Output directory')
@click.option('--seed', type=int, help='Random seed for reproducibility')
@click.option('--quality', type=click.Choice(['low', 'medium', 'high']), default='high', help='Image quality')
@click.option('--parallel', type=int, default=3, help='Number of parallel generations')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def ref_exp(yaml_file, iterations, output, seed, quality, parallel, verbose):
    """Run reference experiments from a YAML file.
    
    Generate multiple image variations based on parameterized prompts
    defined in the YAML file.
    """
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Display header
    console.print(Panel.fit(
        "[bold blue]Reference Experiments[/bold blue]\n"
        "Systematic prompt variation testing",
        border_style="blue"
    ))
    
    # Parse YAML file
    console.print(f"\n[yellow]Loading experiment file:[/yellow] {yaml_file}")
    parser = RefExpParser()
    
    try:
        experiment = parser.parse_file(yaml_file)
        console.print(f"[green]✓[/green] Loaded experiment: [bold]{experiment.name}[/bold]")
        
        if experiment.description:
            console.print(f"  {experiment.description}")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to parse file: {e}")
        sys.exit(1)
    
    # Display experiment info
    info_table = Table(title="Experiment Configuration", show_header=False)
    info_table.add_column("Setting", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Variables", str(len(experiment.variables)))
    info_table.add_row("Total Combinations", str(experiment.get_total_combinations()))
    
    # Parse iterations
    if iterations == 'all':
        num_iterations = experiment.get_total_combinations()
        mode = 'all'
    else:
        try:
            num_iterations = int(iterations)
            mode = 'random'
        except ValueError:
            console.print(f"[red]Invalid iterations value: {iterations}[/red]")
            sys.exit(1)
    
    info_table.add_row("Iterations", str(num_iterations))
    info_table.add_row("Mode", mode)
    info_table.add_row("Output Directory", output)
    info_table.add_row("Quality", quality)
    info_table.add_row("Parallel Workers", str(parallel))
    
    if seed is not None:
        info_table.add_row("Random Seed", str(seed))
    
    console.print("\n", info_table, "\n")
    
    # Override quality if specified
    if 'quality' not in experiment.settings:
        experiment.settings['quality'] = quality
    
    # Generate combinations
    console.print("[yellow]Generating combinations...[/yellow]")
    generator = CombinationGenerator()
    
    try:
        combinations = generator.generate_combinations(
            experiment,
            limit=num_iterations if mode != 'all' else None,
            seed=seed,
            mode=mode
        )
        console.print(f"[green]✓[/green] Generated {len(combinations)} combinations")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to generate combinations: {e}")
        sys.exit(1)
    
    # Show sample combinations
    if len(combinations) <= 5:
        console.print("\n[cyan]Combinations to generate:[/cyan]")
        for i, combo in enumerate(combinations, 1):
            console.print(f"  {i}. {combo.prompt[:100]}...")
    else:
        console.print(f"\n[cyan]Sample combinations (showing 3 of {len(combinations)}):[/cyan]")
        for i in [0, len(combinations)//2, -1]:
            console.print(f"  {combinations[i].id}. {combinations[i].prompt[:100]}...")
    
    # Confirm generation
    if not click.confirm("\nProceed with image generation?", default=True):
        console.print("[yellow]Generation cancelled[/yellow]")
        sys.exit(0)
    
    # Run async generation
    console.print("\n[yellow]Starting image generation...[/yellow]")
    asyncio.run(generate_images_async(
        experiment, combinations, output, parallel, verbose
    ))


async def generate_images_async(
    experiment,
    combinations,
    output_dir,
    parallel,
    verbose
):
    """Async function to generate images with progress display."""
    
    # Initialize components
    try:
        # Load config
        config_loader = ConfigLoader()
        config = config_loader.load()
        
        # Create Gemini client
        client = GeminiClient()
        
        # Create generator
        generator = RefExpImageGenerator(
            gemini_client=client,
            config=config,
            output_dir=output_dir
        )
        
        # Create session
        session = ExperimentSession(
            experiment=experiment,
            generated_images=[],
            start_time=None,  # Will be set in __post_init__
            total_combinations=len(combinations)
        )
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize: {e}")
        sys.exit(1)
    
    # Generate images with progress bar
    generated_images = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task(
            f"Generating {len(combinations)} images...",
            total=len(combinations)
        )
        
        def update_progress(percent, message):
            progress.update(task, completed=int(percent / 100 * len(combinations)))
        
        try:
            # Generate images
            generated_images = await generator.generate_images(
                experiment,
                combinations,
                session,
                progress_callback=update_progress,
                parallel=parallel
            )
            
            session.generated_images = generated_images
            session.mark_complete()
            
        except Exception as e:
            console.print(f"\n[red]✗[/red] Generation failed: {e}")
            session.add_error(str(e))
    
    # Display results
    console.print(f"\n[green]✓[/green] Generated {len(generated_images)}/{len(combinations)} images")
    
    if session.errors and verbose:
        console.print("\n[red]Errors encountered:[/red]")
        for error in session.errors[:5]:  # Show first 5 errors
            console.print(f"  • {error}")
    
    # Update reference document
    console.print("\n[yellow]Updating reference document...[/yellow]")
    try:
        tracker = ReferenceTracker(output_dir=Path(output_dir).parent.parent)
        tracker.update_reference_doc(session)
        console.print("[green]✓[/green] Updated reference_images.md")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to update reference document: {e}")
    
    # Show summary
    summary_table = Table(title="Generation Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")
    
    summary_table.add_row("Total Attempted", str(len(combinations)))
    summary_table.add_row("Successfully Generated", str(session.generated_count))
    summary_table.add_row("Failed", str(session.failed_count))
    summary_table.add_row("Success Rate", f"{session.get_success_rate():.1f}%")
    summary_table.add_row("Duration", f"{session.get_duration():.1f} seconds")
    
    if session.generated_images:
        output_path = Path(output_dir) / f"session_{session.session_id}"
        summary_table.add_row("Output Location", str(output_path))
    
    console.print("\n", summary_table)
    
    # Final message
    if session.generated_count > 0:
        console.print(f"\n[green]✓[/green] Experiment complete! Images saved to {output_dir}")
    else:
        console.print("\n[red]✗[/red] No images were generated")
        sys.exit(1)