#!/usr/bin/env python3
"""
📋 PAGE TRADES - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Liste détaillée des trades BUY/SELL - AUCUNE DONNÉE TEST
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Trades - Satochi Bot",
    page_icon="📋",
    layout="wide"
)

try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class TradesPage:
    """Page des trades - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
    
    def run(self):
        """Lance la page trades avec DONNÉES RÉELLES uniquement"""
        
        st.title("📋 Historique des Trades (Firebase)")
        st.markdown("### 🔥 DONNÉES EN TEMPS RÉEL - AUCUNE SIMULATION")
        st.markdown("---")
        
        # Auto-refresh simple (optionnel - utilisateur peut actualiser manuellement)
        auto_refresh = st.checkbox("Auto-refresh", value=False, key="trades_auto_refresh")
        if auto_refresh:
            st.info("🔄 Mode auto-refresh activé - Utilisez F5 ou le bouton 🔄 Actualiser pour rafraîchir")
        
        # Récupération des données RÉELLES
        try:
            trades_data = self.firebase_config.get_trades_data(limit=200)
            positions_data = self.firebase_config.get_positions_data()
            
            if not trades_data:
                st.warning("📭 Aucune donnée de trade trouvée dans Firebase")
                st.info("🔄 Le bot n'a peut-être pas encore effectué de trades")
                return
            
            # Filtres RÉELS
            self._display_real_filters(trades_data)
            
            # Métriques RÉELLES
            self._display_real_metrics(trades_data)
            
            # Graphiques RÉELS
            col1, col2 = st.columns(2)
            
            with col1:
                self._display_real_timeline(trades_data)
            
            with col2:
                self._display_real_distribution(trades_data)
            
            # Positions RÉELLES
            st.subheader("🔄 Positions Actuellement Ouvertes (Firebase)")
            self._display_real_positions(positions_data)
            
            # Historique RÉEL
            st.subheader("📊 Historique Complet des Trades (Firebase)")
            self._display_real_history(trades_data)
            
        except Exception as e:
            st.error(f"❌ Erreur récupération données Firebase: {e}")
            st.info("🔧 Vérifiez la configuration Firebase")
    
    def _display_real_filters(self, trades_data):
        """Filtres basés sur les VRAIES données"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Extraction des vraies paires depuis les données
        real_symbols = list(set([trade.get('symbol', 'UNKNOWN') for trade in trades_data]))
        
        with col1:
            self.selected_period = st.selectbox(
                "Période",
                ["Aujourd'hui", "7 derniers jours", "30 derniers jours", "Tout l'historique"],
                index=2
            )
        
        with col2:
            self.selected_pairs = st.multiselect(
                "Paires (Vraies données)",
                real_symbols,
                default=real_symbols[:5] if len(real_symbols) > 5 else real_symbols
            )
        
        with col3:
            self.trade_status = st.selectbox(
                "Status",
                ["Tous", "FILLED", "PARTIAL", "CANCELLED"],
                index=0
            )
        
        with col4:
            self.min_pnl = st.number_input("PnL minimum", value=0.0)
    
    def _display_real_metrics(self, trades_data):
        """Métriques RÉELLES calculées depuis Firebase"""
        st.subheader("📊 Métriques Réelles (Firebase)")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        try:
            # Calculs RÉELS
            total_trades = len(trades_data)
            winning_trades = len([t for t in trades_data if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in trades_data if t.get('pnl', 0) < 0])
            winrate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = sum([trade.get('pnl', 0) for trade in trades_data])
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
            
            pnls = [trade.get('pnl', 0) for trade in trades_data if 'pnl' in trade]
            best_trade = max(pnls) if pnls else 0
            worst_trade = min(pnls) if pnls else 0
            
            with col1:
                st.metric(
                    label="📈 Total Trades",
                    value=total_trades,
                    delta="Réels"
                )
            
            with col2:
                st.metric(
                    label="🎯 Winrate",
                    value=f"{winrate:.1f}%",
                    delta=f"{winning_trades}W/{losing_trades}L"
                )
            
            with col3:
                st.metric(
                    label="💰 P&L Total",
                    value=f"{total_pnl:+.2f} USDC",
                    delta=f"Moy: {avg_pnl:+.2f}"
                )
            
            with col4:
                # Calcul durée moyenne RÉELLE
                durations = []
                for trade in trades_data:
                    if 'entry_time' in trade and 'exit_time' in trade:
                        try:
                            entry = datetime.fromisoformat(trade['entry_time'].replace('Z', ''))
                            exit = datetime.fromisoformat(trade['exit_time'].replace('Z', ''))
                            duration = (exit - entry).total_seconds() / 60  # minutes
                            durations.append(duration)
                        except:
                            continue
                
                avg_duration = np.mean(durations) if durations else 0
                median_duration = np.median(durations) if durations else 0
                
                st.metric(
                    label="⏱️ Durée Moyenne",
                    value=f"{avg_duration:.0f}min",
                    delta=f"Médiane: {median_duration:.0f}min"
                )
            
            with col5:
                st.metric(
                    label="🚀 Meilleur Trade",
                    value=f"+{best_trade:.2f} USDC",
                    delta="Record"
                )
            
            with col6:
                st.metric(
                    label="💥 Pire Trade",
                    value=f"{worst_trade:+.2f} USDC",
                    delta="Loss max"
                )
                
        except Exception as e:
            st.error(f"❌ Erreur calcul métriques: {e}")
    
    def _display_real_timeline(self, trades_data):
        """Timeline RÉELLE des trades"""
        st.subheader("📈 Timeline Réelle des Trades")
        
        try:
            if not trades_data:
                st.warning("📭 Aucune donnée")
                return
            
            df = pd.DataFrame(trades_data)
            
            if 'timestamp' in df.columns and 'pnl' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['cumulative_pnl'] = df['pnl'].cumsum()
                
                fig = px.scatter(
                    df, 
                    x='timestamp', 
                    y='pnl',
                    color='symbol',
                    size=abs(df['pnl']) + 1,
                    title="P&L par Trade (Firebase)",
                    hover_data=['symbol', 'side', 'quantity']
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Colonnes manquantes pour timeline")
                
        except Exception as e:
            st.error(f"❌ Erreur timeline: {e}")
    
    def _display_real_distribution(self, trades_data):
        """Distribution RÉELLE des P&L"""
        st.subheader("📊 Distribution P&L Réelle")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'pnl' in df.columns:
                fig = px.histogram(
                    df, 
                    x='pnl',
                    title="Distribution des P&L (Firebase)",
                    nbins=20,
                    labels={'pnl': 'P&L (USDC)', 'count': 'Nombre de trades'}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Colonne 'pnl' manquante")
                
        except Exception as e:
            st.error(f"❌ Erreur distribution: {e}")
    
    def _display_real_positions(self, positions_data):
        """Positions RÉELLES ouvertes"""
        try:
            if not positions_data:
                st.info("📭 Aucune position ouverte actuellement")
                return
            
            df = pd.DataFrame(positions_data)
            
            # Colonnes disponibles
            available_columns = list(df.columns)
            st.info(f"📊 Colonnes disponibles: {', '.join(available_columns)}")
            
            # Affichage des données
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur positions: {e}")
    
    def _display_real_history(self, trades_data):
        """Historique RÉEL complet"""
        try:
            if not trades_data:
                st.info("📭 Aucun historique de trade")
                return
            
            df = pd.DataFrame(trades_data)
            
            # Tri par timestamp décroissant
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=False)
            
            # Affichage avec toutes les colonnes disponibles
            st.info(f"📊 {len(df)} trades trouvés dans Firebase")
            st.dataframe(df, use_container_width=True, height=400)
            
            # Export CSV
            if st.button("💾 Télécharger CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger",
                    data=csv,
                    file_name=f"satochi_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
        except Exception as e:
            st.error(f"❌ Erreur historique: {e}")

# Lancement de la page
if __name__ == "__main__":
    page = TradesPage()
    page.run()
