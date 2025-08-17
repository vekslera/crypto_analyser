#!/usr/bin/env python3
"""
Analyze modified files for Single Responsibility and Dependency Inversion compliance
"""

import sys
import os
import ast
import inspect
from typing import List, Dict, Tuple

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class SRPDIPAnalyzer:
    """Analyzer for Single Responsibility and Dependency Inversion principles"""
    
    def __init__(self):
        self.violations = []
        self.compliances = []
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a single file for SRP and DIP compliance"""
        
        print(f"\n{'='*60}")
        print(f"ANALYZING: {os.path.relpath(file_path, project_root)}")
        print(f"{'='*60}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            file_analysis = {
                'file': file_path,
                'classes': [],
                'functions': [],
                'imports': [],
                'violations': [],
                'compliances': []
            }
            
            # Analyze imports
            self._analyze_imports(tree, file_analysis)
            
            # Analyze classes and methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._analyze_class(node, file_analysis, content)
                elif isinstance(node, ast.FunctionDef) and not self._is_method(node, tree):
                    self._analyze_function(node, file_analysis)
            
            self._print_analysis(file_analysis)
            return file_analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {'file': file_path, 'error': str(e)}
    
    def _analyze_imports(self, tree: ast.AST, analysis: Dict):
        """Analyze import dependencies"""
        imports = []
        concrete_imports = []
        abstract_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}"
                    imports.append(full_name)
                    
                    # Check if importing interfaces (abstract) vs implementations (concrete)
                    if 'interface' in module.lower() or alias.name.endswith('Interface'):
                        abstract_imports.append(full_name)
                    elif 'implementation' in module.lower() or 'provider' in module.lower():
                        concrete_imports.append(full_name)
        
        analysis['imports'] = imports
        analysis['abstract_imports'] = abstract_imports
        analysis['concrete_imports'] = concrete_imports
    
    def _analyze_class(self, node: ast.ClassDef, analysis: Dict, content: str):
        """Analyze class for SRP and DIP compliance"""
        
        class_info = {
            'name': node.name,
            'methods': [],
            'responsibilities': [],
            'dependencies': [],
            'violations': [],
            'compliances': []
        }
        
        # Analyze methods
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        
        for method in methods:
            method_info = self._analyze_method(method, class_info)
            class_info['methods'].append(method_info)
        
        # Identify responsibilities from method names and docstrings
        self._identify_responsibilities(class_info, node, content)
        
        # Check SRP compliance
        self._check_srp_compliance(class_info)
        
        # Check DIP compliance
        self._check_dip_compliance(class_info, analysis)
        
        analysis['classes'].append(class_info)
    
    def _analyze_method(self, node: ast.FunctionDef, class_info: Dict) -> Dict:
        """Analyze individual method"""
        
        method_info = {
            'name': node.name,
            'is_private': node.name.startswith('_'),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'calls_external': False,
            'responsibility': self._infer_responsibility(node.name)
        }
        
        # Check for external calls
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                method_info['calls_external'] = True
                break
        
        return method_info
    
    def _identify_responsibilities(self, class_info: Dict, node: ast.ClassDef, content: str):
        """Identify class responsibilities from methods and docstring"""
        
        responsibilities = set()
        
        # From class name
        if 'Scheduler' in node.name:
            responsibilities.add('scheduling')
        if 'Provider' in node.name:
            responsibilities.add('data_provision')
        if 'Service' in node.name:
            responsibilities.add('business_logic')
        if 'Repository' in node.name:
            responsibilities.add('data_persistence')
        
        # From method names
        for method in class_info['methods']:
            method_name = method['name']
            if 'fetch' in method_name or 'get' in method_name:
                responsibilities.add('data_fetching')
            if 'store' in method_name or 'save' in method_name:
                responsibilities.add('data_storage')
            if 'calculate' in method_name or 'compute' in method_name:
                responsibilities.add('computation')
            if 'validate' in method_name or 'check' in method_name:
                responsibilities.add('validation')
            if 'schedule' in method_name or 'start' in method_name or 'stop' in method_name:
                responsibilities.add('lifecycle_management')
            if 'combine' in method_name or 'merge' in method_name:
                responsibilities.add('data_combination')
        
        class_info['responsibilities'] = list(responsibilities)
    
    def _check_srp_compliance(self, class_info: Dict):
        """Check Single Responsibility Principle compliance"""
        
        responsibilities = class_info['responsibilities']
        
        if len(responsibilities) <= 1:
            class_info['compliances'].append({
                'principle': 'SRP',
                'status': 'COMPLIANT',
                'reason': f"Class has {len(responsibilities)} responsibility: {responsibilities}"
            })
        elif len(responsibilities) == 2:
            # Allow some reasonable combinations
            acceptable_combinations = [
                {'data_fetching', 'data_combination'},
                {'data_storage', 'computation'},
                {'scheduling', 'lifecycle_management'}
            ]
            
            if set(responsibilities) in acceptable_combinations:
                class_info['compliances'].append({
                    'principle': 'SRP',
                    'status': 'ACCEPTABLE',
                    'reason': f"Acceptable combination: {responsibilities}"
                })
            else:
                class_info['violations'].append({
                    'principle': 'SRP',
                    'severity': 'MODERATE',
                    'reason': f"Multiple responsibilities: {responsibilities}"
                })
        else:
            class_info['violations'].append({
                'principle': 'SRP',
                'severity': 'HIGH',
                'reason': f"Too many responsibilities ({len(responsibilities)}): {responsibilities}"
            })
    
    def _check_dip_compliance(self, class_info: Dict, file_analysis: Dict):
        """Check Dependency Inversion Principle compliance"""
        
        concrete_deps = len(file_analysis['concrete_imports'])
        abstract_deps = len(file_analysis['abstract_imports'])
        
        if abstract_deps > concrete_deps:
            class_info['compliances'].append({
                'principle': 'DIP',
                'status': 'COMPLIANT',
                'reason': f"Depends on abstractions ({abstract_deps}) more than concretions ({concrete_deps})"
            })
        elif abstract_deps == concrete_deps and abstract_deps > 0:
            class_info['compliances'].append({
                'principle': 'DIP',
                'status': 'ACCEPTABLE',
                'reason': f"Balanced abstractions ({abstract_deps}) and concretions ({concrete_deps})"
            })
        elif concrete_deps > 0 and abstract_deps == 0:
            class_info['violations'].append({
                'principle': 'DIP',
                'severity': 'HIGH', 
                'reason': f"Only concrete dependencies ({concrete_deps}), no abstractions"
            })
        else:
            class_info['compliances'].append({
                'principle': 'DIP',
                'status': 'NEUTRAL',
                'reason': "No significant dependencies detected"
            })
    
    def _infer_responsibility(self, method_name: str) -> str:
        """Infer responsibility from method name"""
        if 'fetch' in method_name or 'get' in method_name:
            return 'data_access'
        elif 'store' in method_name or 'save' in method_name:
            return 'data_persistence'
        elif 'calculate' in method_name or 'compute' in method_name:
            return 'computation'
        elif 'validate' in method_name or 'check' in method_name:
            return 'validation'
        elif 'start' in method_name or 'stop' in method_name or 'schedule' in method_name:
            return 'lifecycle'
        else:
            return 'business_logic'
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is a class method"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False
    
    def _analyze_function(self, node: ast.FunctionDef, analysis: Dict):
        """Analyze standalone function"""
        analysis['functions'].append({
            'name': node.name,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'responsibility': self._infer_responsibility(node.name)
        })
    
    def _print_analysis(self, analysis: Dict):
        """Print analysis results"""
        
        print(f"\nIMPORTS ANALYSIS:")
        print(f"  Abstract dependencies: {len(analysis['abstract_imports'])}")
        for dep in analysis['abstract_imports']:
            print(f"    ✓ {dep}")
        
        print(f"  Concrete dependencies: {len(analysis['concrete_imports'])}")
        for dep in analysis['concrete_imports']:
            print(f"    • {dep}")
        
        for class_info in analysis['classes']:
            print(f"\nCLASS: {class_info['name']}")
            print(f"  Responsibilities: {class_info['responsibilities']}")
            print(f"  Methods: {len(class_info['methods'])}")
            
            # Print compliances
            for compliance in class_info['compliances']:
                status_symbol = "✓" if compliance['status'] == 'COMPLIANT' else "~" if compliance['status'] == 'ACCEPTABLE' else "?"
                print(f"    {status_symbol} {compliance['principle']}: {compliance['reason']}")
            
            # Print violations
            for violation in class_info['violations']:
                severity_symbol = "⚠️" if violation['severity'] == 'MODERATE' else "❌"
                print(f"    {severity_symbol} {violation['principle']}: {violation['reason']}")
    
    def generate_summary(self, analyses: List[Dict]):
        """Generate overall summary"""
        
        print(f"\n{'='*60}")
        print("OVERALL COMPLIANCE SUMMARY")
        print(f"{'='*60}")
        
        total_classes = sum(len(a['classes']) for a in analyses if 'classes' in a)
        total_violations = 0
        total_compliances = 0
        
        violation_details = []
        compliance_details = []
        
        for analysis in analyses:
            if 'classes' in analysis:
                for class_info in analysis['classes']:
                    for violation in class_info['violations']:
                        total_violations += 1
                        violation_details.append({
                            'file': analysis['file'],
                            'class': class_info['name'],
                            'violation': violation
                        })
                    
                    for compliance in class_info['compliances']:
                        total_compliances += 1
                        compliance_details.append({
                            'file': analysis['file'], 
                            'class': class_info['name'],
                            'compliance': compliance
                        })
        
        print(f"Total classes analyzed: {total_classes}")
        print(f"Compliance items: {total_compliances}")
        print(f"Violations found: {total_violations}")
        
        if total_violations == 0:
            print(f"\n✅ EXCELLENT: No SOLID principle violations detected!")
        elif total_violations <= 2:
            print(f"\n⚠️  ACCEPTABLE: Minor violations that can be addressed")
        else:
            print(f"\n❌ NEEDS WORK: Multiple violations requiring attention")
        
        # Detailed breakdown
        if violation_details:
            print(f"\nVIOLATIONS BREAKDOWN:")
            srp_violations = [v for v in violation_details if v['violation']['principle'] == 'SRP']
            dip_violations = [v for v in violation_details if v['violation']['principle'] == 'DIP']
            
            if srp_violations:
                print(f"  Single Responsibility Principle: {len(srp_violations)} violations")
                for v in srp_violations:
                    print(f"    • {v['class']}: {v['violation']['reason']}")
            
            if dip_violations:
                print(f"  Dependency Inversion Principle: {len(dip_violations)} violations") 
                for v in dip_violations:
                    print(f"    • {v['class']}: {v['violation']['reason']}")


def main():
    """Analyze all modified files"""
    
    # Files to analyze (the ones we modified)
    files_to_analyze = [
        'server/optimal_scheduler.py',
        'server/services/crypto_service.py', 
        'server/implementations/hybrid_provider.py',
        'server/dependency_container.py'
    ]
    
    analyzer = SRPDIPAnalyzer()
    analyses = []
    
    print("SOLID PRINCIPLES COMPLIANCE ANALYSIS")
    print("Analyzing modified files for SRP and DIP compliance...")
    
    for file_path in files_to_analyze:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            analysis = analyzer.analyze_file(full_path)
            analyses.append(analysis)
        else:
            print(f"Warning: File not found: {file_path}")
    
    # Generate summary
    analyzer.generate_summary(analyses)


if __name__ == "__main__":
    main()