"""
Service de monitoring intelligent pour OpenHands.
Détecte les anomalies et envoie des alertes.
"""

import re
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque


@dataclass
class Alert:
    """Représente une alerte détectée."""
    severity: str  # 'warning', 'error', 'critical'
    type: str      # 'loop', 'compilation_error', 'timeout', 'resource'
    message: str
    details: Dict
    timestamp: datetime


class OpenHandsMonitor:
    """
    Moniteur intelligent pour détecter les anomalies dans les sessions OpenHands.
    """
    
    # Patterns d'erreurs de compilation
    COMPILATION_ERROR_PATTERNS = [
        r"error:\s+(.+)",
        r"SyntaxError:",
        r"TypeError:",
        r"ImportError:",
        r"ModuleNotFoundError:",
        r"FileNotFoundError:",
        r"PermissionError:",
        r"ConnectionError:",
    ]
    
    # Patterns de boucles potentielles
    LOOP_PATTERNS = [
        r"Retrying",
        r"Retrying.*attempt \d+",
        r"Same error again",
        r"Repeating the same operation",
        r"Loop detected",
    ]
    
    def __init__(self, max_error_history: int = 10, loop_threshold: int = 3):
        self.max_error_history = max_error_history
        self.loop_threshold = loop_threshold
        self.error_history: deque = deque(maxlen=max_error_history)
        self.last_command: Optional[str] = None
        self.command_count: Dict[str, int] = {}
        self.alerts: List[Alert] = []
        
    def analyze_log(self, log_message: str) -> List[Alert]:
        """Analyse un message de log et retourne les alertes potentielles."""
        alerts = []
        timestamp = datetime.now()
        
        # Vérifier les erreurs de compilation
        for pattern in self.COMPILATION_ERROR_PATTERNS:
            match = re.search(pattern, log_message, re.IGNORECASE)
            if match:
                error_type = match.group(0) if match.lastindex is None else match.group(1)
                self.error_history.append({
                    'type': 'compilation',
                    'error': error_type,
                    'timestamp': timestamp
                })
                
                # Vérifier si c'est une boucle d'erreurs
                loop_alert = self._check_error_loop(error_type)
                if loop_alert:
                    alerts.append(loop_alert)
                break
        
        # Vérifier les boucles potentielles
        for pattern in self.LOOP_PATTERNS:
            if re.search(pattern, log_message, re.IGNORECASE):
                self._track_command_pattern(log_message)
                loop_alert = self._check_command_loop()
                if loop_alert:
                    alerts.append(loop_alert)
                break
        
        # Vérifier les timeouts
        if 'timeout' in log_message.lower() or 'timed out' in log_message.lower():
            alerts.append(Alert(
                severity='warning',
                type='timeout',
                message=f"Timeout détecté: {log_message[:100]}...",
                details={'log': log_message},
                timestamp=timestamp
            ))
        
        # Vérifier la mémoire
        if 'memory' in log_message.lower() and ('exceeded' in log_message.lower() or 'error' in log_message.lower()):
            alerts.append(Alert(
                severity='critical',
                type='resource',
                message="Consommation mémoire excessive",
                details={'log': log_message},
                timestamp=timestamp
            ))
        
        self.alerts.extend(alerts)
        return alerts
    
    def _check_error_loop(self, current_error: str) -> Optional[Alert]:
        """Vérifie si la même erreur se répète."""
        recent_errors = [
            e['error'] for e in list(self.error_history)[-self.loop_threshold:]
        ]
        
        if len(recent_errors) >= self.loop_threshold:
            # Compter les occurrences de l'erreur actuelle
            occurrences = recent_errors.count(current_error)
            
            if occurrences >= self.loop_threshold:
                return Alert(
                    severity='critical',
                    type='loop',
                    message=f"Erreur répétée {occurrences} fois: {current_error[:100]}",
                    details={
                        'error': current_error,
                        'occurrences': occurrences,
                        'recent_errors': recent_errors
                    },
                    timestamp=datetime.now()
                )
        return None
    
    def _track_command_pattern(self, log_message: str):
        """Suit les patterns de commandes pour détecter les boucles."""
        # Extraire les commandes potentielles du log
        command_match = re.search(r"\$ (.+)|python (.+\.py)", log_message)
        if command_match:
            command = command_match.group(0)
            
            # Compter les occurrences
            self.command_count[command] = self.command_count.get(command, 0) + 1
            self.last_command = command
    
    def _check_command_loop(self) -> Optional[Alert]:
        """Vérifie si une commande se répète excessivement."""
        if not self.command_count:
            return None
        
        max_count = max(self.command_count.values())
        
        if max_count >= 5:  # 5 répétitions = boucle
            most_repeated = max(self.command_count, key=self.command_count.get)
            return Alert(
                severity='warning',
                type='loop',
                message=f"Commande potentiellement en boucle: {most_repeated[:100]}",
                details={
                    'command': most_repeated,
                    'count': max_count
                },
                timestamp=datetime.now()
            )
        return None
    
    def get_summary(self) -> Dict:
        """Retourne un résumé de l'état du monitor."""
        return {
            'total_alerts': len(self.alerts),
            'alerts_by_severity': {
                'warning': len([a for a in self.alerts if a.severity == 'warning']),
                'error': len([a for a in self.alerts if a.severity == 'error']),
                'critical': len([a for a in self.alerts if a.severity == 'critical']),
            },
            'recent_errors': list(self.error_history)[-5:],
            'command_stats': self.command_count,
        }
    
    def reset(self):
        """Réinitialise le moniteur."""
        self.error_history.clear()
        self.last_command = None
        self.command_count = {}
        self.alerts.clear()


# Instance singleton par session
_session_monitors: Dict[int, OpenHandsMonitor] = {}


def get_monitor(session_id: int) -> OpenHandsMonitor:
    """Récupère ou crée un moniteur pour une session."""
    if session_id not in _session_monitors:
        _session_monitors[session_id] = OpenHandsMonitor()
    return _session_monitors[session_id]


def remove_monitor(session_id: int):
    """Supprime le moniteur d'une session."""
    if session_id in _session_monitors:
        del _session_monitors[session_id]


def analyze_openhands_log(session_id: int, log_message: str) -> List[Alert]:
    """Analyse un log et retourne les alertes."""
    monitor = get_monitor(session_id)
    return monitor.analyze_log(log_message)