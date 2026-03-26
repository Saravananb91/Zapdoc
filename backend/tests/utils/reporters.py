"""
Test result reporting utilities.
Generates comprehensive test reports, accuracy summaries, and performance metrics.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import csv


# ===========================
# Test Result Aggregation
# ===========================

class TestReporter:
    """Aggregates and reports test results."""
    
    def __init__(self):
        self.results = {
            "unit_tests": [],
            "integration_tests": [],
            "accuracy_tests": [],
            "performance_tests": []
        }
        self.start_time = datetime.now()
    
    def add_result(self, category: str, test_name: str, passed: bool, details: Dict[str, Any] = None):
        """Add test result."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        if category in self.results:
            self.results[category].append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics."""
        summary = {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "categories": {}
        }
        
        for category, tests in self.results.items():
            if tests:
                passed_count = sum(1 for t in tests if t["passed"])
                summary["categories"][category] = {
                    "total": len(tests),
                    "passed": passed_count,
                    "failed": len(tests) - passed_count,
                    "pass_rate": passed_count / len(tests) if tests else 0
                }
        
        return summary
    
    def save_to_json(self, output_path: Path):
        """Save results to JSON file."""
        summary = self.get_summary()
        summary["detailed_results"] = self.results
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    
    def save_to_csv(self, output_path: Path):
        """Save results to CSV file."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Test Name", "Passed", "Timestamp"])
            
            for category, tests in self.results.items():
                for test in tests:
                    writer.writerow([
                        category,
                        test["test_name"],
                        "PASS" if test["passed"] else "FAIL",
                        test["timestamp"]
                    ])


# ===========================
# Accuracy Metrics Reporter
# ===========================

class AccuracyReporter:
    """Specialized reporter for accuracy metrics."""
    
    def __init__(self):
        self.accuracy_results = []
    
    def add_accuracy_result(
        self,
        document_name: str,
        field_accuracy: float,
        item_accuracy: float,
        summary_accuracy: float,
        details: Dict[str, Any] = None
    ):
        """Add accuracy test result."""
        result = {
            "document": document_name,
            "field_accuracy": field_accuracy,
            "item_accuracy": item_accuracy,
            "summary_accuracy": summary_accuracy,
            "overall_accuracy": (field_accuracy + item_accuracy + summary_accuracy) / 3,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.accuracy_results.append(result)
    
    def get_aggregate_metrics(self) -> Dict[str, float]:
        """Calculate aggregate accuracy metrics."""
        if not self.accuracy_results:
            return {}
        
        total_docs = len(self.accuracy_results)
        
        return {
            "documents_tested": total_docs,
            "avg_field_accuracy": sum(r["field_accuracy"] for r in self.accuracy_results) / total_docs,
            "avg_item_accuracy": sum(r["item_accuracy"] for r in self.accuracy_results) / total_docs,
            "avg_summary_accuracy": sum(r["summary_accuracy"] for r in self.accuracy_results) / total_docs,
            "avg_overall_accuracy": sum(r["overall_accuracy"] for r in self.accuracy_results) / total_docs,
            "min_accuracy": min(r["overall_accuracy"] for r in self.accuracy_results),
            "max_accuracy": max(r["overall_accuracy"] for r in self.accuracy_results)
        }
    
    def save_report(self, output_path: Path):
        """Save accuracy report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "aggregate_metrics": self.get_aggregate_metrics(),
            "individual_results": self.accuracy_results
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    
    def print_summary(self):
        """Print accuracy summary to console."""
        metrics = self.get_aggregate_metrics()
        
        print("\n" + "="*60)
        print("ACCURACY TEST SUMMARY")
        print("="*60)
        print(f"Documents Tested: {metrics.get('documents_tested', 0)}")
        print(f"Avg Field Accuracy: {metrics.get('avg_field_accuracy', 0):.2%}")
        print(f"Avg Item Accuracy: {metrics.get('avg_item_accuracy', 0):.2%}")
        print(f"Avg Summary Accuracy: {metrics.get('avg_summary_accuracy', 0):.2%}")
        print(f"Avg Overall Accuracy: {metrics.get('avg_overall_accuracy', 0):.2%}")
        print("="*60 + "\n")


# ===========================
# Performance Metrics Reporter
# ===========================

class PerformanceReporter:
    """Reporter for performance and load test metrics."""
    
    def __init__(self):
        self.performance_results = []
    
    def add_performance_result(
        self,
        test_name: str,
        duration_ms: float,
        throughput: float = None,
        memory_mb: float = None,
        details: Dict[str, Any] = None
    ):
        """Add performance test result."""
        result = {
            "test_name": test_name,
            "duration_ms": duration_ms,
            "throughput": throughput,
            "memory_mb": memory_mb,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.performance_results.append(result)
    
    def get_benchmark_summary(self) -> Dict[str, Any]:
        """Get benchmark statistics."""
        if not self.performance_results:
            return {}
        
        durations = [r["duration_ms"] for r in self.performance_results if r["duration_ms"]]
        
        return {
            "total_tests": len(self.performance_results),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "p50_duration_ms": sorted(durations)[len(durations) // 2] if durations else 0,
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "p99_duration_ms": sorted(durations)[int(len(durations) * 0.99)] if durations else 0
        }
    
    def save_report(self, output_path: Path):
        """Save performance report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_benchmark_summary(),
            "detailed_results": self.performance_results
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    
    def print_summary(self):
        """Print performance summary to console."""
        summary = self.get_benchmark_summary()
        
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Avg Duration: {summary.get('avg_duration_ms', 0):.2f}ms")
        print(f"Min Duration: {summary.get('min_duration_ms', 0):.2f}ms")
        print(f"Max Duration: {summary.get('max_duration_ms', 0):.2f}ms")
        print(f"P50 Duration: {summary.get('p50_duration_ms', 0):.2f}ms")
        print(f"P95 Duration: {summary.get('p95_duration_ms', 0):.2f}ms")
        print(f"P99 Duration: {summary.get('p99_duration_ms', 0):.2f}ms")
        print("="*60 + "\n")


# ===========================
# Helper Functions
# ===========================

def generate_html_summary(
    test_results: Dict[str, Any],
    output_path: Path
):
    """
    Generate simple HTML summary report.
    
    Args:
        test_results: Test results dictionary
        output_path: Path to save HTML file
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OCR Test Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .pass {{ color: green; font-weight: bold; }}
            .fail {{ color: red; font-weight: bold; }}
            .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>OCR Agent Test Results</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <h2>Test Results by Category</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Total</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Pass Rate</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for category, stats in test_results.get("categories", {}).items():
        pass_rate = stats.get("pass_rate", 0) * 100
        html_content += f"""
                <tr>
                    <td>{category}</td>
                    <td>{stats.get('total', 0)}</td>
                    <td class="pass">{stats.get('passed', 0)}</td>
                    <td class="fail">{stats.get('failed', 0)}</td>
                    <td>{pass_rate:.1f}%</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def merge_test_reports(report_paths: List[Path], output_path: Path):
    """
    Merge multiple test reports into one.
    
    Args:
        report_paths: List of report file paths
        output_path: Path to save merged report
    """
    merged = {
        "timestamp": datetime.now().isoformat(),
        "reports": []
    }
    
    for report_path in report_paths:
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
                merged["reports"].append({
                    "source": str(report_path),
                    "data": report_data
                })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
