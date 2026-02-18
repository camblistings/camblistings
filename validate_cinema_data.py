#!/usr/bin/env python3
"""
Data validation system for cinema scraper data.
Automatically detects and flags unrealistic data patterns.
"""

import json
from datetime import datetime
from collections import defaultdict

def validate_cinema_data(data_file='website_data_by_cinema.json'):
    """Validate cinema data and flag obvious issues"""
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return {"valid": False, "error": f"Cannot read JSON file: {e}"}
    
    issues = []
    warnings = []
    stats = defaultdict(dict)
    
    for cinema in data.get('cinemas', []):
        cinema_name = cinema.get('name', 'Unknown')
        films = cinema.get('films', [])
        
        # Group films by day
        films_by_day = defaultdict(list)
        for film in films:
            day = film.get('day', 'unknown')
            films_by_day[day].append(film)
        
        stats[cinema_name] = {
            'total_films': len(films),
            'days': len(films_by_day),
            'films_by_day': {day: len(day_films) for day, day_films in films_by_day.items()}
        }
        
        # Check each day for issues
        for day, day_films in films_by_day.items():
            day_issues = []
            
            # Check for unrealistic showtime counts
            for film in day_films:
                showtimes = film.get('showtimes', [])
                title = film.get('title', 'Unknown')
                
                # Flag films with too many showtimes
                if len(showtimes) > 4:
                    issues.append(f"🚨 {cinema_name} - {day}: '{title}' has {len(showtimes)} showtimes (unrealistic)")
                    day_issues.append(f"Too many showtimes: {title} ({len(showtimes)})")
                
                # Flag films with duplicate showtimes
                if len(showtimes) != len(set(showtimes)):
                    issues.append(f"🚨 {cinema_name} - {day}: '{title}' has duplicate showtimes")
                    day_issues.append(f"Duplicate showtimes: {title}")
                
                # Flag films with no showtimes
                if len(showtimes) == 0:
                    warnings.append(f"⚠️  {cinema_name} - {day}: '{title}' has no showtimes")
            
            # Check total film count for the day
            if len(day_films) > 30:
                issues.append(f"🚨 {cinema_name} - {day}: {len(day_films)} films (too many for one day)")
            elif len(day_films) > 20:
                warnings.append(f"⚠️  {cinema_name} - {day}: {len(day_films)} films (high but possible)")
            
            # Check for same film appearing multiple times on same day
            title_counts = defaultdict(int)
            for film in day_films:
                title_counts[film.get('title', 'Unknown')] += 1
            
            duplicates = {title: count for title, count in title_counts.items() if count > 1}
            if duplicates:
                issues.append(f"🚨 {cinema_name} - {day}: Duplicate films: {duplicates}")
    
    # Overall validation
    total_films = sum(cinema['total_films'] for cinema in stats.values())
    if total_films > 500:
        issues.append(f"🚨 Total films across all cinemas: {total_films} (unrealistically high)")
    
    # Generate report
    report = {
        "valid": len(issues) == 0,
        "timestamp": datetime.now().isoformat(),
        "stats": dict(stats),
        "issues": issues,
        "warnings": warnings,
        "summary": {
            "total_issues": len(issues),
            "total_warnings": len(warnings),
            "total_films": total_films
        }
    }
    
    return report

def auto_fix_data(data_file='website_data_by_cinema.json', backup=True):
    """Automatically fix common data issues"""
    
    if backup:
        import shutil
        shutil.copy(data_file, f"{data_file}.backup")
        print(f"📁 Backed up original data to {data_file}.backup")
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Cannot read data file: {e}")
        return False
    
    fixes_applied = []
    
    for cinema in data.get('cinemas', []):
        cinema_name = cinema.get('name', 'Unknown')
        original_films = cinema.get('films', [])
        
        fixed_films = []
        
        for film in original_films:
            title = film.get('title', 'Unknown')
            showtimes = film.get('showtimes', [])
            
            # Fix 1: Remove duplicate showtimes
            unique_showtimes = sorted(list(set(showtimes)))
            if len(unique_showtimes) < len(showtimes):
                fixes_applied.append(f"Removed duplicate showtimes from '{title}'")
                showtimes = unique_showtimes
            
            # Fix 2: Limit showtimes per film (max 3 for regular, max 5 for IMAX)
            max_showtimes = 3 if 'Regular' in cinema_name else 5
            if len(showtimes) > max_showtimes:
                fixes_applied.append(f"Limited '{title}' from {len(showtimes)} to {max_showtimes} showtimes")
                showtimes = showtimes[:max_showtimes]
            
            # Fix 3: Remove films with no showtimes
            if len(showtimes) == 0:
                fixes_applied.append(f"Removed '{title}' (no showtimes)")
                continue
            
            # Update film with fixed showtimes
            film['showtimes'] = showtimes
            film['showtime_count'] = len(showtimes)
            fixed_films.append(film)
        
        # Update cinema films
        cinema['films'] = fixed_films
        fixes_applied.append(f"{cinema_name}: {len(original_films)} → {len(fixed_films)} films")
    
    # Save fixed data
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"   • {fix}")
    
    return True

if __name__ == "__main__":
    print("🔍 Validating cinema data...")
    report = validate_cinema_data()
    
    print(f"\n📊 Validation Results:")
    print(f"   Valid: {'✅' if report['valid'] else '❌'}")
    print(f"   Issues: {report['summary']['total_issues']}")
    print(f"   Warnings: {report['summary']['total_warnings']}")
    print(f"   Total films: {report['summary']['total_films']}")
    
    if report['issues']:
        print(f"\n🚨 Critical Issues:")
        for issue in report['issues']:
            print(f"   {issue}")
    
    if report['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in report['warnings']:
            print(f"   {warning}")
    
    # Auto-fix if there are issues
    if not report['valid']:
        print(f"\n🔧 Auto-fixing data...")
        if auto_fix_data():
            print(f"\n🔍 Re-validating after fixes...")
            new_report = validate_cinema_data()
            print(f"   Valid: {'✅' if new_report['valid'] else '❌'}")
            print(f"   Issues: {new_report['summary']['total_issues']}")
            print(f"   Total films: {new_report['summary']['total_films']}")
    else:
        print(f"\n✅ Data looks good!")
