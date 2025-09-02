"""CLI commands for reference management."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import ConfigLoader
from src.references.manager import ReferenceManager
from src.references.storage import ReferenceStorage
from src.references.validators import (
    ReferenceValidator,
    ImageValidator,
    ConsistencyValidator,
    ValidationReport
)
from src.api import GeminiClient

# Setup console
console = Console()
logger = logging.getLogger(__name__)


@click.group()
def reference():
    """Manage reference images for consistent character and location appearance."""
    pass


@reference.command()
@click.option('--name', '-n', required=True, help='Character name')
@click.option('--description', '-d', required=True, help='Character description')
@click.option('--poses', '-p', multiple=True, help='Poses to generate')
@click.option('--expressions', '-e', multiple=True, help='Expressions to generate')
@click.option('--age', help='Age range (e.g., "young adult", "middle-aged")')
@click.option('--traits', multiple=True, help='Physical traits')
@click.option('--style', '-s', help='Style guide name to use')
@click.option('--output', '-o', default='references', help='Output directory')
@click.option('--generate/--no-generate', default=True, help='Generate images automatically')
def create_character(name, description, poses, expressions, age, traits, style, output, generate):
    """Create a new character reference."""
    console.print(Panel.fit(
        f"[bold cyan]Creating Character Reference[/bold cyan]\n"
        f"Name: {name}",
        border_style="cyan"
    ))
    
    try:
        # Setup storage and manager
        storage = ReferenceStorage(output)
        
        if generate:
            # Setup Gemini client for generation
            config = ConfigLoader()
            client = GeminiClient(api_key=config.get('gemini_api_key'))
            manager = ReferenceManager(storage=storage, gemini_client=client)
        else:
            manager = ReferenceManager(storage=storage)
        
        # Create character reference
        with console.status("[yellow]Creating character reference...[/yellow]"):
            character = manager.create_reference(
                ref_type="character",
                name=name,
                description=description,
                poses=list(poses) if poses else ["standing"],
                expressions=list(expressions) if expressions else ["neutral"],
                age_range=age if age else "",
                physical_traits=list(traits) if traits else []
            )
        
        console.print(f"[green]✓[/green] Character reference created: {name}")
        
        # Generate images if requested
        if generate:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                poses_list = list(poses) if poses else ["standing"]
                expressions_list = list(expressions) if expressions else ["neutral"]
                task = progress.add_task(
                    f"Generating images for {name}...",
                    total=len(poses_list) * len(expressions_list)
                )
                
                # Run async generation
                async def generate_images():
                    style_guide = None
                    if style:
                        style_guide = manager.get_reference("styleguide", style)
                    
                    return await manager.generate_character(
                        name=name,
                        description=description,
                        poses=list(poses) if poses else ["standing"],
                        expressions=list(expressions) if expressions else ["neutral"],
                        age_range=age,
                        physical_traits=list(traits) if traits else [],
                        style_guide=style_guide
                    )
                
                character = asyncio.run(generate_images())
                progress.update(task, completed=len(poses_list) * len(expressions_list))
            
            console.print(f"[green]✓[/green] Generated {len(character.images)} images")
        
        # Display character info
        table = Table(title=f"Character: {name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", character.name)
        table.add_row("Description", character.description)
        table.add_row("Poses", ", ".join(character.poses))
        table.add_row("Expressions", ", ".join(character.expressions))
        if character.age_range:
            table.add_row("Age Range", character.age_range)
        if character.physical_traits:
            table.add_row("Traits", ", ".join(character.physical_traits))
        if character.images:
            table.add_row("Images", f"{len(character.images)} generated")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create character: {e}")
        raise click.Abort()


@reference.command()
@click.option('--name', '-n', required=True, help='Location name')
@click.option('--description', '-d', required=True, help='Location description')
@click.option('--type', '-t', type=click.Choice(['interior', 'exterior', 'mixed']), 
              default='exterior', help='Location type')
@click.option('--angles', '-a', multiple=True, help='Camera angles')
@click.option('--lighting', '-l', multiple=True, help='Lighting conditions')
@click.option('--time', multiple=True, help='Times of day')
@click.option('--style', '-s', help='Style guide name to use')
@click.option('--output', '-o', default='references', help='Output directory')
@click.option('--generate/--no-generate', default=True, help='Generate images automatically')
def create_location(name, description, type, angles, lighting, time, style, output, generate):
    """Create a new location reference."""
    console.print(Panel.fit(
        f"[bold cyan]Creating Location Reference[/bold cyan]\n"
        f"Name: {name}",
        border_style="cyan"
    ))
    
    try:
        # Setup storage and manager
        storage = ReferenceStorage(output)
        
        if generate:
            config = ConfigLoader()
            client = GeminiClient(api_key=config.get('gemini_api_key'))
            manager = ReferenceManager(storage=storage, gemini_client=client)
        else:
            manager = ReferenceManager(storage=storage)
        
        # Create location reference
        with console.status("[yellow]Creating location reference...[/yellow]"):
            location = manager.create_reference(
                ref_type="location",
                name=name,
                description=description,
                location_type=type,
                angles=list(angles) if angles else ["wide-shot"],
                lighting_conditions=list(lighting) if lighting else ["daylight"],
                time_of_day=list(time) if time else []
            )
        
        console.print(f"[green]✓[/green] Location reference created: {name}")
        
        # Generate images if requested
        if generate:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"Generating images for {name}...",
                    total=len(angles) * len(lighting)
                )
                
                async def generate_images():
                    style_guide = None
                    if style:
                        style_guide = manager.get_reference("styleguide", style)
                    
                    return await manager.generate_location(
                        name=name,
                        description=description,
                        location_type=type,
                        angles=list(angles),
                        lighting_conditions=list(lighting),
                        time_of_day=list(time) if time else [],
                        style_guide=style_guide
                    )
                
                location = asyncio.run(generate_images())
                progress.update(task, completed=len(angles) * len(lighting))
            
            console.print(f"[green]✓[/green] Generated {len(location.images)} images")
        
        # Display location info
        table = Table(title=f"Location: {name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", location.name)
        table.add_row("Description", location.description)
        table.add_row("Type", location.location_type)
        table.add_row("Angles", ", ".join(location.angles))
        table.add_row("Lighting", ", ".join(location.lighting_conditions))
        if location.time_of_day:
            table.add_row("Times", ", ".join(location.time_of_day))
        if location.images:
            table.add_row("Images", f"{len(location.images)} generated")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create location: {e}")
        raise click.Abort()


@reference.command()
@click.option('--name', '-n', required=True, help='Object name')
@click.option('--description', '-d', required=True, help='Object description')
@click.option('--category', '-c', help='Object category (e.g., "weapon", "tool", "artifact")')
@click.option('--views', '-v', multiple=True, help='Views to generate')
@click.option('--states', '-s', multiple=True, help='States (e.g., "new", "damaged")')
@click.option('--style', help='Style guide name to use')
@click.option('--output', '-o', default='references', help='Output directory')
@click.option('--generate/--no-generate', default=True, help='Generate images automatically')
def create_object(name, description, category, views, states, style, output, generate):
    """Create a new object reference."""
    console.print(Panel.fit(
        f"[bold cyan]Creating Object Reference[/bold cyan]\n"
        f"Name: {name}",
        border_style="cyan"
    ))
    
    try:
        # Setup storage and manager
        storage = ReferenceStorage(output)
        
        if generate:
            config = ConfigLoader()
            client = GeminiClient(api_key=config.get('gemini_api_key'))
            manager = ReferenceManager(storage=storage, gemini_client=client)
        else:
            manager = ReferenceManager(storage=storage)
        
        # Create object reference
        with console.status("[yellow]Creating object reference...[/yellow]"):
            obj = manager.create_reference(
                ref_type="object",
                name=name,
                description=description,
                category=category if category else "",
                views=list(views) if views else ["front"],
                states=list(states) if states else ["normal"]
            )
        
        console.print(f"[green]✓[/green] Object reference created: {name}")
        
        # Generate images if requested
        if generate:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"Generating images for {name}...",
                    total=len(views) * len(states)
                )
                
                async def generate_images():
                    style_guide = None
                    if style:
                        style_guide = manager.get_reference("styleguide", style)
                    
                    return await manager.generate_object(
                        name=name,
                        description=description,
                        category=category if category else "",
                        views=list(views),
                        states=list(states),
                        style_guide=style_guide
                    )
                
                obj = asyncio.run(generate_images())
                progress.update(task, completed=len(views) * len(states))
            
            console.print(f"[green]✓[/green] Generated {len(obj.images)} images")
        
        # Display object info
        table = Table(title=f"Object: {name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", obj.name)
        table.add_row("Description", obj.description)
        if obj.category:
            table.add_row("Category", obj.category)
        table.add_row("Views", ", ".join(obj.views))
        table.add_row("States", ", ".join(obj.states))
        if obj.images:
            table.add_row("Images", f"{len(obj.images)} generated")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create object: {e}")
        raise click.Abort()


@reference.command()
@click.option('--name', '-n', required=True, help='Style guide name')
@click.option('--description', '-d', required=True, help='Style description')
@click.option('--art-style', '-a', required=True, help='Art style (e.g., "comic-book", "manga")')
@click.option('--colors', '-c', multiple=True, help='Color palette (hex codes)')
@click.option('--line-style', help='Line style (e.g., "bold", "thin", "sketchy")')
@click.option('--lighting', help='Lighting style (e.g., "dramatic", "soft", "flat")')
@click.option('--output', '-o', default='references', help='Output directory')
def create_style(name, description, art_style, colors, line_style, lighting, output):
    """Create a new style guide."""
    console.print(Panel.fit(
        f"[bold cyan]Creating Style Guide[/bold cyan]\n"
        f"Name: {name}",
        border_style="cyan"
    ))
    
    try:
        # Setup storage and manager
        storage = ReferenceStorage(output)
        manager = ReferenceManager(storage=storage)
        
        # Create style guide
        with console.status("[yellow]Creating style guide...[/yellow]"):
            style = manager.create_reference(
                ref_type="styleguide",
                name=name,
                description=description,
                art_style=art_style,
                color_palette=list(colors) if colors else [],
                line_style=line_style if line_style else "",
                lighting_style=lighting if lighting else ""
            )
        
        console.print(f"[green]✓[/green] Style guide created: {name}")
        
        # Display style info
        table = Table(title=f"Style Guide: {name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", style.name)
        table.add_row("Description", style.description)
        table.add_row("Art Style", style.art_style)
        if style.color_palette:
            table.add_row("Colors", ", ".join(style.color_palette))
        if style.line_style:
            table.add_row("Line Style", style.line_style)
        if style.lighting_style:
            table.add_row("Lighting", style.lighting_style)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create style guide: {e}")
        raise click.Abort()


@reference.command()
@click.option('--type', '-t', type=click.Choice(['all', 'character', 'location', 'object', 'styleguide']),
              default='all', help='Reference type to list')
@click.option('--tags', multiple=True, help='Filter by tags')
@click.option('--storage', '-s', default='references', help='Storage directory')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed information')
def list(type, tags, storage, detailed):
    """List available references."""
    try:
        # Setup storage and manager
        storage_obj = ReferenceStorage(storage)
        manager = ReferenceManager(storage=storage_obj)
        
        # Get references
        ref_type = None if type == 'all' else type
        refs = manager.list_references(ref_type=ref_type, tags=list(tags) if tags else None)
        
        # Display results
        if not any(refs.values()):
            console.print("[yellow]No references found[/yellow]")
            return
        
        for rtype, names in refs.items():
            if not names:
                continue
            
            # Create table for this type
            title = f"{rtype.title()} References"
            if tags:
                title += f" (filtered by tags: {', '.join(tags)})"
            
            table = Table(title=title)
            table.add_column("Name", style="cyan")
            if detailed:
                table.add_column("Description", style="white")
                table.add_column("Tags", style="yellow")
                table.add_column("Images", style="green")
                table.add_column("Updated", style="blue")
            
            for name in names:
                ref = manager.get_reference(rtype, name)
                if ref:
                    if detailed:
                        tags_str = ", ".join(ref.tags) if ref.tags else "-"
                        images_str = str(len(ref.images)) if hasattr(ref, 'images') else "-"
                        updated_str = ref.updated_at.strftime("%Y-%m-%d %H:%M")
                        table.add_row(
                            ref.name,
                            ref.description[:50] + "..." if len(ref.description) > 50 else ref.description,
                            tags_str,
                            images_str,
                            updated_str
                        )
                    else:
                        table.add_row(ref.name)
            
            console.print(table)
            console.print()
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list references: {e}")
        raise click.Abort()


@reference.command()
@click.argument('ref_type', type=click.Choice(['character', 'location', 'object', 'styleguide']))
@click.argument('name')
@click.option('--description', '-d', help='New description')
@click.option('--add-tag', multiple=True, help='Add tags')
@click.option('--remove-tag', multiple=True, help='Remove tags')
@click.option('--storage', '-s', default='references', help='Storage directory')
def update(ref_type, name, description, add_tag, remove_tag, storage):
    """Update an existing reference."""
    console.print(f"[yellow]Updating {ref_type}: {name}[/yellow]")
    
    try:
        # Setup storage and manager
        storage_obj = ReferenceStorage(storage)
        manager = ReferenceManager(storage=storage_obj)
        
        # Get existing reference
        ref = manager.get_reference(ref_type, name)
        if not ref:
            console.print(f"[red]✗[/red] Reference not found: {name}")
            raise click.Abort()
        
        # Build updates
        updates = {}
        if description:
            updates['description'] = description
        
        # Handle tags
        current_tags = set(ref.tags) if ref.tags else set()
        if add_tag:
            current_tags.update(add_tag)
        if remove_tag:
            current_tags.difference_update(remove_tag)
        if add_tag or remove_tag:
            updates['tags'] = list(current_tags)
        
        # Apply updates
        if updates:
            updated_ref = manager.update_reference(ref_type, name, updates)
            console.print(f"[green]✓[/green] Updated {ref_type}: {name}")
            
            # Show updated fields
            table = Table(title="Updated Fields")
            table.add_column("Field", style="cyan")
            table.add_column("New Value", style="white")
            
            for field, value in updates.items():
                if field == 'tags':
                    value = ", ".join(value) if value else "(none)"
                table.add_row(field.title(), str(value))
            
            console.print(table)
        else:
            console.print("[yellow]No updates specified[/yellow]")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to update reference: {e}")
        raise click.Abort()


@reference.command()
@click.argument('ref_type', type=click.Choice(['character', 'location', 'object', 'styleguide']))
@click.argument('name')
@click.option('--storage', '-s', default='references', help='Storage directory')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
def delete(ref_type, name, storage, force):
    """Delete a reference."""
    try:
        # Setup storage and manager
        storage_obj = ReferenceStorage(storage)
        manager = ReferenceManager(storage=storage_obj)
        
        # Check if exists
        ref = manager.get_reference(ref_type, name)
        if not ref:
            console.print(f"[red]✗[/red] Reference not found: {name}")
            raise click.Abort()
        
        # Confirm deletion
        if not force:
            confirm = Confirm.ask(
                f"[yellow]Delete {ref_type} '{name}'?[/yellow]",
                default=False
            )
            if not confirm:
                console.print("[yellow]Deletion cancelled[/yellow]")
                return
        
        # Delete reference
        manager.delete_reference(ref_type, name)
        console.print(f"[green]✓[/green] Deleted {ref_type}: {name}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to delete reference: {e}")
        raise click.Abort()


@reference.command()
@click.option('--storage', '-s', default='references', help='Storage directory')
@click.option('--days', '-d', default=30, help='Days unused before cleanup')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without deleting')
def cleanup(storage, days, dry_run):
    """Clean up unused references."""
    console.print(Panel.fit(
        f"[bold yellow]Reference Cleanup[/bold yellow]\n"
        f"Removing references unused for {days} days",
        border_style="yellow"
    ))
    
    try:
        # Setup storage and manager
        storage_obj = ReferenceStorage(storage)
        manager = ReferenceManager(storage=storage_obj)
        
        # Find unused references
        with console.status("[yellow]Finding unused references...[/yellow]"):
            if dry_run:
                # For dry run, just list what would be deleted
                import datetime
                from datetime import timedelta
                cutoff = datetime.datetime.now() - timedelta(days=days)
                
                refs = manager.list_references()
                unused = []
                
                for rtype, names in refs.items():
                    for name in names:
                        ref = manager.get_reference(rtype, name)
                        if ref and ref.updated_at < cutoff:
                            unused.append((rtype, name, ref.updated_at))
            else:
                # Actually perform cleanup
                removed = manager.cleanup_unused_references(days_unused=days)
                unused = [(t, n, None) for t, n in removed]
        
        if not unused:
            console.print("[green]✓[/green] No unused references found")
            return
        
        # Display results
        table = Table(title="Unused References")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Last Updated", style="yellow")
        
        for rtype, name, updated in unused:
            updated_str = updated.strftime("%Y-%m-%d") if updated else "N/A"
            table.add_row(rtype, name, updated_str)
        
        console.print(table)
        
        if dry_run:
            console.print(f"\n[yellow]Dry run - {len(unused)} references would be deleted[/yellow]")
        else:
            console.print(f"\n[green]✓[/green] Deleted {len(unused)} unused references")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to cleanup references: {e}")
        raise click.Abort()