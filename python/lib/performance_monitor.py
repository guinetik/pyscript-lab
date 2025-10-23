"""
Performance Monitor - Adaptive performance tuning for RL training

Monitors decision loop timing and automatically adjusts parameters
based on machine capabilities.

Author: Guinetik
"""

import time
from js import console, window
import numpy as np


class PerformanceMonitor:
    """
    Monitors training performance and suggests optimal settings.
    Tracks decision timing, detects bottlenecks, and provides tuning recommendations.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.decision_times = []  # Last N decision times
        self.max_samples = 100  # Keep last 100 samples
        
        # Timing breakdowns
        self.observe_times = []
        self.decide_times = []
        self.act_times = []
        
        # Performance metrics
        self.avg_decision_time = 0
        self.p95_decision_time = 0
        self.target_fps = 15  # Default target
        
        # Auto-tuning state
        self.auto_tune_enabled = False
        self.last_tune_time = 0
        self.tune_interval = 10  # Tune every 10 seconds
        
        print("📊 PerformanceMonitor initialized")
    
    def start_timing(self):
        """Start timing a decision cycle."""
        return time.time()
    
    def record_observe(self, start_time):
        """Record observation timing."""
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        self.observe_times.append(elapsed)
        if len(self.observe_times) > self.max_samples:
            self.observe_times.pop(0)
        return time.time()
    
    def record_decide(self, start_time):
        """Record decision timing."""
        elapsed = (time.time() - start_time) * 1000
        self.decide_times.append(elapsed)
        if len(self.decide_times) > self.max_samples:
            self.decide_times.pop(0)
        return time.time()
    
    def record_act(self, start_time):
        """Record action timing."""
        elapsed = (time.time() - start_time) * 1000
        self.act_times.append(elapsed)
        if len(self.act_times) > self.max_samples:
            self.act_times.pop(0)
        return time.time()
    
    def record_decision(self, start_time):
        """Record total decision cycle timing."""
        elapsed = (time.time() - start_time) * 1000
        self.decision_times.append(elapsed)
        if len(self.decision_times) > self.max_samples:
            self.decision_times.pop(0)
        
        # Update metrics
        if len(self.decision_times) >= 10:
            self.avg_decision_time = np.mean(self.decision_times)
            self.p95_decision_time = np.percentile(self.decision_times, 95)
    
    def get_stats(self) -> dict:
        """
        Get performance statistics.
        
        Returns:
            dict: Performance metrics
        """
        if len(self.decision_times) < 10:
            return {
                'status': 'warming_up',
                'samples': len(self.decision_times)
            }
        
        return {
            'status': 'ready',
            'samples': len(self.decision_times),
            'avg_decision_ms': float(self.avg_decision_time),
            'p95_decision_ms': float(self.p95_decision_time),
            'avg_observe_ms': float(np.mean(self.observe_times)) if self.observe_times else 0,
            'avg_decide_ms': float(np.mean(self.decide_times)) if self.decide_times else 0,
            'avg_act_ms': float(np.mean(self.act_times)) if self.act_times else 0,
            'current_fps': float(1000 / self.avg_decision_time) if self.avg_decision_time > 0 else 0,
            'target_fps': self.target_fps,
            'utilization': float(self.avg_decision_time / (1000 / self.target_fps)) if self.target_fps > 0 else 0
        }
    
    def recommend_settings(self) -> dict:
        """
        Recommend optimal settings based on measured performance.
        
        Returns:
            dict: Recommended settings with rationale
        """
        stats = self.get_stats()
        
        if stats['status'] == 'warming_up':
            return {
                'status': 'insufficient_data',
                'message': 'Collecting performance data...'
            }
        
        utilization = stats['utilization']
        avg_time = stats['avg_decision_ms']
        
        recommendations = {
            'current_performance': stats,
            'recommendations': []
        }
        
        # Recommend faster decision rate if CPU has headroom
        if utilization < 0.5:  # Using less than 50% of available time
            max_fps = int(1000 / (avg_time * 1.5))  # Leave 50% headroom
            max_fps = min(max_fps, 60)  # Cap at 60 FPS (emulator limit)
            
            recommendations['recommendations'].append({
                'type': 'increase_fps',
                'current_fps': stats['target_fps'],
                'recommended_fps': max_fps,
                'reason': f"CPU utilization is only {utilization*100:.1f}%. Your machine can handle faster training!",
                'expected_speedup': f"{max_fps / stats['target_fps']:.1f}x faster"
            })
        
        elif utilization > 0.9:  # Using more than 90% of available time
            recommended_fps = int(1000 / (avg_time * 1.2))  # Add 20% headroom
            
            recommendations['recommendations'].append({
                'type': 'decrease_fps',
                'current_fps': stats['target_fps'],
                'recommended_fps': recommended_fps,
                'reason': f"CPU utilization is {utilization*100:.1f}%. Risk of lag/jitter.",
                'impact': 'More stable training, slightly slower'
            })
        
        # Recommend network size adjustments
        if stats['avg_decide_ms'] > 5:  # Network forward pass is slow
            recommendations['recommendations'].append({
                'type': 'reduce_network',
                'reason': f"Neural network forward pass is slow ({stats['avg_decide_ms']:.1f}ms)",
                'suggestion': "Consider reducing hidden layer size (32 → 24 or 16)"
            })
        
        elif stats['avg_decide_ms'] < 2 and utilization < 0.5:  # Network is fast, CPU has headroom
            recommendations['recommendations'].append({
                'type': 'increase_network',
                'reason': f"Neural network is fast ({stats['avg_decide_ms']:.1f}ms) and CPU has headroom",
                'suggestion': "Consider increasing hidden layer size (32 → 48 or 64) for more learning capacity"
            })
        
        # Recommend vision optimization
        if stats['avg_observe_ms'] > 8:  # Vision extraction is slow
            recommendations['recommendations'].append({
                'type': 'optimize_vision',
                'reason': f"Vision extraction is slow ({stats['avg_observe_ms']:.1f}ms)",
                'suggestion': "Consider reducing vision grid size (24×7 → 16×7)"
            })
        
        return recommendations
    
    def auto_tune(self, agent):
        """
        Automatically adjust agent settings based on performance.
        
        Args:
            agent: PlayerAgent instance to tune
        
        Returns:
            dict: Applied changes
        """
        recommendations = self.recommend_settings()
        
        if recommendations.get('status') == 'insufficient_data':
            return None
        
        changes = []
        
        for rec in recommendations['recommendations']:
            if rec['type'] == 'increase_fps':
                new_fps = rec['recommended_fps']
                # Update target FPS
                self.target_fps = new_fps
                changes.append(f"Increased FPS: {rec['current_fps']} → {new_fps}")
                print(f"⚡ Auto-tune: Increased decision rate to {new_fps} FPS")
            
            elif rec['type'] == 'decrease_fps':
                new_fps = rec['recommended_fps']
                self.target_fps = new_fps
                changes.append(f"Decreased FPS: {rec['current_fps']} → {new_fps}")
                print(f"🐌 Auto-tune: Decreased decision rate to {new_fps} FPS")
        
        return {
            'applied': changes,
            'recommendations': recommendations
        }
    
    def get_optimal_interval(self) -> int:
        """
        Get optimal decision interval in milliseconds based on current performance.
        
        Returns:
            int: Milliseconds between decisions
        """
        if self.avg_decision_time == 0:
            return 67  # Default 15 FPS
        
        # Target interval = actual time * 1.5 (50% headroom)
        optimal_interval = int(self.avg_decision_time * 1.5)
        
        # Clamp to reasonable range
        optimal_interval = max(16, min(optimal_interval, 100))  # 10-60 FPS range
        
        return optimal_interval
    
    def print_report(self):
        """Print detailed performance report."""
        stats = self.get_stats()
        
        if stats['status'] == 'warming_up':
            print(f"⏳ Warming up... ({stats['samples']}/10 samples)")
            return
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE REPORT")
        print("="*60)
        print(f"Decision Rate: {stats['current_fps']:.1f} FPS (target: {stats['target_fps']} FPS)")
        print(f"CPU Utilization: {stats['utilization']*100:.1f}%")
        print(f"\nTiming Breakdown:")
        print(f"  Observe: {stats['avg_observe_ms']:.2f}ms")
        print(f"  Decide:  {stats['avg_decide_ms']:.2f}ms")
        print(f"  Act:     {stats['avg_act_ms']:.2f}ms")
        print(f"  TOTAL:   {stats['avg_decision_ms']:.2f}ms (avg), {stats['p95_decision_ms']:.2f}ms (95th)")
        print(f"\nOptimal interval: {self.get_optimal_interval()}ms")
        
        # Get recommendations
        recs = self.recommend_settings()
        if recs.get('recommendations'):
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recs['recommendations'], 1):
                print(f"\n{i}. {rec['type'].upper()}")
                print(f"   {rec['reason']}")
                if 'suggestion' in rec:
                    print(f"   → {rec['suggestion']}")
                if 'expected_speedup' in rec:
                    print(f"   → Expected speedup: {rec['expected_speedup']}")
        
        print("="*60 + "\n")


# Export to builtins for use by agent
import builtins
builtins.PerformanceMonitor = PerformanceMonitor


