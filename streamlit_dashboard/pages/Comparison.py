#!/usr/bin/env python3
"""
<<<<<<< HEAD
🔄 PAGE COMPARISON - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Comparaison de performances - AUCUNE DONNÉE TEST
=======
🔍 PAGE COMPARAISON BINANCE/FIREBASE
Compare les données collectées par le service binance-live avec Firebase
>>>>>>> feature/clean-config
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
<<<<<<< HEAD
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="Comparison - Satochi Bot",
    page_icon="🔄",
    layout="wide"
)

try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class ComparisonPage:
    """Comparison - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
    
    def run(self):
        """Comparaisons basées UNIQUEMENT sur Firebase"""
        
        st.title("🔄 Comparaison de Performances (Firebase)")
        st.markdown("### 🔥 COMPARAISONS RÉELLES - AUCUNE SIMULATION")
        st.markdown("---")
        
        # Auto-refresh simple (optionnel - utilisateur peut actualiser manuellement)
        auto_refresh = st.checkbox("Auto-refresh", value=False, key="comparison_auto_refresh")
        if auto_refresh:
            st.info("🔄 Mode auto-refresh activé - Utilisez F5 ou le bouton 🔄 Actualiser pour rafraîchir")
        
        try:
            # Récupération données RÉELLES
            trades_data = self.firebase_config.get_trades_data(limit=1000)
            
            if not trades_data:
                st.warning("📭 Aucune donnée pour comparaison dans Firebase")
                st.info("🔄 Attendez que le bot génère plus de données")
                return
            
            # Sélection des périodes de comparaison
            self._display_comparison_controls()
            
            # Comparaison par paires RÉELLES
            self._display_real_pairs_comparison(trades_data)
            
            # Comparaison temporelle RÉELLE
            self._display_real_time_comparison(trades_data)
            
            # Comparaison stratégies RÉELLE (si disponible)
            self._display_real_strategy_comparison(trades_data)
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison Firebase: {e}")
    
    def _display_comparison_controls(self):
        """Contrôles de comparaison"""
        st.subheader("⚙️ Paramètres de Comparaison")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.comparison_type = st.selectbox(
                "Type de comparaison",
                ["Par Paire", "Par Période", "Par Stratégie"],
                index=0
            )
        
        with col2:
            self.metric_type = st.selectbox(
                "Métrique principale",
                ["P&L Total", "Winrate", "Profit Factor", "Sharpe Ratio"],
                index=0
            )
        
        with col3:
            self.time_period = st.selectbox(
                "Période d'analyse",
                ["7 derniers jours", "30 derniers jours", "Tout l'historique"],
                index=1
            )
    
    def _display_real_pairs_comparison(self, trades_data):
        """Comparaison par paires RÉELLES"""
        st.subheader("📊 Comparaison par Paire (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'symbol' not in df.columns or 'pnl' not in df.columns:
                st.warning("📊 Données symbol/pnl manquantes")
                return
            
            # Groupement par paire
            pair_stats = df.groupby('symbol').agg({
                'pnl': ['sum', 'mean', 'count', 'std'],
                'symbol': 'count'
            }).round(4)
            
            pair_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades', 'Volatilité', 'Total']
            pair_stats = pair_stats.drop('Total', axis=1)
            
            # Calcul Winrate par paire
            winrates = df.groupby('symbol').apply(
                lambda x: (x['pnl'] > 0).sum() / len(x) * 100
            ).round(1)
            pair_stats['Winrate %'] = winrates
            
            # Calcul Profit Factor par paire
            def calculate_profit_factor(group):
                wins = group[group['pnl'] > 0]['pnl'].sum()
                losses = abs(group[group['pnl'] < 0]['pnl'].sum())
                return wins / losses if losses > 0 else float('inf')
            
            profit_factors = df.groupby('symbol').apply(calculate_profit_factor).round(2)
            pair_stats['Profit Factor'] = profit_factors
            
            # Tri par métrique sélectionnée
            sort_column_map = {
                "P&L Total": "PnL Total",
                "Winrate": "Winrate %",
                "Profit Factor": "Profit Factor",
                "Sharpe Ratio": "PnL Moyen"  # Approximation
            }
            sort_column = sort_column_map.get(self.metric_type, "PnL Total")
            pair_stats = pair_stats.sort_values(sort_column, ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(pair_stats, use_container_width=True)
            
            with col2:
                # Graphique de comparaison
                fig = px.bar(
                    x=pair_stats.index,
                    y=pair_stats[sort_column],
                    title=f"{self.metric_type} par Paire (Firebase)",
                    labels={'y': self.metric_type, 'x': 'Paire'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison paires: {e}")
    
    def _display_real_time_comparison(self, trades_data):
        """Comparaison temporelle RÉELLE"""
        st.subheader("⏰ Comparaison Temporelle (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'timestamp' not in df.columns or 'pnl' not in df.columns:
                st.warning("📊 Données timestamp/pnl manquantes")
                return
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filtrage par période
            if self.time_period == "7 derniers jours":
                cutoff = datetime.now() - timedelta(days=7)
                df = df[df['timestamp'] > cutoff]
            elif self.time_period == "30 derniers jours":
                cutoff = datetime.now() - timedelta(days=30)
                df = df[df['timestamp'] > cutoff]
            
            if len(df) == 0:
                st.info("📭 Aucune donnée dans la période sélectionnée")
                return
            
            # Comparaison par jour
            df['date'] = df['timestamp'].dt.date
            daily_stats = df.groupby('date').agg({
                'pnl': ['sum', 'mean', 'count']
            }).round(2)
            
            daily_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades']
            daily_stats['Winrate %'] = df.groupby('date').apply(
                lambda x: (x['pnl'] > 0).sum() / len(x) * 100
            ).round(1)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique évolution journalière
                fig = px.bar(
                    x=daily_stats.index,
                    y=daily_stats['PnL Total'],
                    title="P&L Journalier (Firebase)",
                    color=daily_stats['PnL Total'],
                    color_continuous_scale=['red', 'gray', 'green']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Graphique winrate journalier
                fig = px.line(
                    x=daily_stats.index,
                    y=daily_stats['Winrate %'],
                    title="Winrate Journalier (Firebase)",
                    markers=True
                )
                fig.add_hline(y=50, line_dash="dash", line_color="gray")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Table des stats journalières
            st.dataframe(daily_stats.sort_index(ascending=False), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison temporelle: {e}")
    
    def _display_real_strategy_comparison(self, trades_data):
        """Comparaison stratégies RÉELLE"""
        st.subheader("🎯 Comparaison Stratégies (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            # Vérifier si on a des données de stratégie
            if 'strategy' in df.columns:
                strategy_stats = df.groupby('strategy').agg({
                    'pnl': ['sum', 'mean', 'count', 'std']
                }).round(4)
                
                strategy_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades', 'Volatilité']
                
                # Calculs additionnels
                winrates = df.groupby('strategy').apply(
                    lambda x: (x['pnl'] > 0).sum() / len(x) * 100
                ).round(1)
                strategy_stats['Winrate %'] = winrates
                
                st.dataframe(strategy_stats, use_container_width=True)
                
                # Graphique comparaison stratégies
                fig = px.bar(
                    x=strategy_stats.index,
                    y=strategy_stats['PnL Total'],
                    title="P&L par Stratégie (Firebase)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # Analyse par type de trade (BUY/SELL)
                if 'side' in df.columns:
                    side_stats = df.groupby('side').agg({
                        'pnl': ['sum', 'mean', 'count']
                    }).round(4)
                    
                    side_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades']
                    
                    winrates = df.groupby('side').apply(
                        lambda x: (x['pnl'] > 0).sum() / len(x) * 100
                    ).round(1)
                    side_stats['Winrate %'] = winrates
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.dataframe(side_stats, use_container_width=True)
                    
                    with col2:
                        fig = px.pie(
                            values=side_stats['PnL Total'],
                            names=side_stats.index,
                            title="Répartition P&L par Type (Firebase)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Pas de données de stratégie ou de side disponibles")
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison stratégies: {e}")

# Lancement de la page
if __name__ == "__main__":
    page = ComparisonPage()
    page.run()
=======
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
import json

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from firebase_logger import FirebaseLogger
    from config import APIConfig
except ImportError as e:
    st.error(f"❌ Erreur import: {e}")
    st.stop()


class BinanceFirebaseComparison:
    """Classe pour comparer les données Binance/Firebase"""
    
    def __init__(self):
        self.firebase_logger = None
        self.setup_firebase()
        
    def setup_firebase(self):
        """Configuration Firebase"""
        try:
            self.firebase_logger = FirebaseLogger()
            if hasattr(self.firebase_logger, 'db') and self.firebase_logger.db:
                st.success("🔥 Firebase connecté avec succès")
            else:
                st.error("❌ Erreur connexion Firebase")
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
    
    def get_binance_live_data(self):
        """Récupère les données de la collection binance_live"""
        try:
            if not self.firebase_logger or not self.firebase_logger.db:
                return None, None, None, None
            
            # Account info
            account_doc = self.firebase_logger.db.collection('binance_live').document('account_info').get()
            account_data = account_doc.to_dict() if account_doc.exists else None
            
            # Recent trades
            trades_doc = self.firebase_logger.db.collection('binance_live').document('recent_trades').get()
            trades_data = trades_doc.to_dict() if trades_doc.exists else None
            
            # Open orders
            orders_doc = self.firebase_logger.db.collection('binance_live').document('open_orders').get()
            orders_data = orders_doc.to_dict() if orders_doc.exists else None
            
            # Health status
            health_doc = self.firebase_logger.db.collection('binance_live').document('health').get()
            health_data = health_doc.to_dict() if health_doc.exists else None
            
            return account_data, trades_data, orders_data, health_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération données binance_live: {e}")
            return None, None, None, None
    
    def get_bot_trades_data(self):
        """Récupère les données des trades du bot principal"""
        try:
            if not self.firebase_logger or not self.firebase_logger.db:
                return []
            
            # Récupérer les trades des dernières 24h
            trades_ref = self.firebase_logger.db.collection('trades')
            trades_query = trades_ref.order_by('timestamp', direction='DESCENDING').limit(100)
            trades_docs = trades_query.get()
            
            trades_data = []
            for doc in trades_docs:
                trade = doc.to_dict()
                trade['id'] = doc.id
                trades_data.append(trade)
            
            return trades_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération trades bot: {e}")
            return []
    
    def display_service_status(self, health_data):
        """Affiche le statut du service binance-live"""
        st.subheader("🔍 Statut du Service Binance Live")
        
        if not health_data:
            st.error("❌ Aucune donnée de santé trouvée")
            st.info("💡 Le service binance-live n'est peut-être pas démarré")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = health_data.get('status', 'unknown')
            if status == 'healthy':
                st.metric("🟢 Statut", "En ligne")
            else:
                st.metric("🔴 Statut", "Hors ligne")
        
        with col2:
            cycle_count = health_data.get('cycle_count', 0)
            st.metric("🔄 Cycles", cycle_count)
        
        with col3:
            pairs_count = health_data.get('monitored_pairs_count', 0)
            st.metric("📊 Paires", pairs_count)
        
        with col4:
            last_check = health_data.get('timestamp', 'Inconnu')
            if last_check != 'Inconnu':
                try:
                    check_time = datetime.fromisoformat(last_check)
                    time_ago = datetime.now() - check_time
                    if time_ago.total_seconds() < 300:  # 5 minutes
                        st.metric("⏰ Dernière vérif", "Récente")
                    else:
                        st.metric("⚠️ Dernière vérif", f"Il y a {int(time_ago.total_seconds()/60)}min")
                except:
                    st.metric("⏰ Dernière vérif", "Inconnue")
            else:
                st.metric("⏰ Dernière vérif", "Inconnue")
    
    def display_account_comparison(self, account_data):
        """Compare les informations de compte"""
        st.subheader("💼 Comparaison des Comptes")
        
        if not account_data:
            st.error("❌ Aucune donnée de compte Binance Live trouvée")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 Données Binance Live**")
            
            balances = account_data.get('balances', [])
            if balances:
                df_binance = pd.DataFrame(balances)
                df_binance = df_binance[df_binance['total'] > 0].sort_values('total', ascending=False)
                
                # Affichage des principales balances
                st.dataframe(
                    df_binance[['asset', 'free', 'locked', 'total']],
                    use_container_width=True,
                    height=300
                )
                
                total_value = account_data.get('total_value_usdc_approx', 0)
                st.metric("💰 Valeur totale (approx)", f"{total_value:.2f} USDC")
            else:
                st.info("Aucune balance trouvée")
        
        with col2:
            st.write("**🤖 Données Bot Trading**")
            
            # Ici on pourrait récupérer les données du bot principal
            # Pour l'instant, affichage placeholder
            st.info("🔄 Intégration avec les données du bot principal à venir")
            
            # Métadonnées du compte Binance Live
            st.write("**ℹ️ Métadonnées**")
            can_trade = account_data.get('canTrade', False)
            can_withdraw = account_data.get('canWithdraw', False)
            account_type = account_data.get('accountType', 'Unknown')
            
            st.write(f"• Trading autorisé: {'✅' if can_trade else '❌'}")
            st.write(f"• Retrait autorisé: {'✅' if can_withdraw else '❌'}")
            st.write(f"• Type de compte: {account_type}")
    
    def display_trades_comparison(self, trades_data, bot_trades):
        """Compare les trades collectés vs les trades du bot"""
        st.subheader("🔄 Comparaison des Trades")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 Trades Binance Live (Dernières 6h)**")
            
            if trades_data and trades_data.get('trades'):
                binance_trades = trades_data['trades']
                
                # Statistiques
                total_trades = len(binance_trades)
                buy_trades = len([t for t in binance_trades if t.get('isBuyer', False)])
                sell_trades = total_trades - buy_trades
                
                col1a, col1b, col1c = st.columns(3)
                col1a.metric("📈 Total", total_trades)
                col1b.metric("🟢 Achats", buy_trades)
                col1c.metric("🔴 Ventes", sell_trades)
                
                # DataFrame des trades récents
                if binance_trades:
                    df_binance_trades = pd.DataFrame(binance_trades[:20])  # 20 derniers
                    if not df_binance_trades.empty:
                        display_cols = ['symbol', 'price', 'qty', 'time', 'isBuyer']
                        available_cols = [col for col in display_cols if col in df_binance_trades.columns]
                        st.dataframe(
                            df_binance_trades[available_cols],
                            use_container_width=True,
                            height=300
                        )
            else:
                st.info("Aucun trade collecté dans les dernières 6h")
        
        with col2:
            st.write("**🤖 Trades du Bot (Dernières 24h)**")
            
            if bot_trades:
                # Statistiques des trades du bot
                bot_total = len(bot_trades)
                completed_trades = len([t for t in bot_trades if t.get('status') == 'COMPLETED'])
                
                col2a, col2b = st.columns(2)
                col2a.metric("📊 Total Bot", bot_total)
                col2b.metric("✅ Complétés", completed_trades)
                
                # DataFrame des trades du bot
                df_bot_trades = pd.DataFrame(bot_trades[:20])
                if not df_bot_trades.empty:
                    display_cols = ['pair', 'side', 'price', 'quantity', 'status']
                    available_cols = [col for col in display_cols if col in df_bot_trades.columns]
                    st.dataframe(
                        df_bot_trades[available_cols],
                        use_container_width=True,
                        height=300
                    )
            else:
                st.info("Aucun trade du bot trouvé")
    
    def display_orders_comparison(self, orders_data):
        """Affiche les ordres ouverts"""
        st.subheader("📋 Ordres Ouverts")
        
        if not orders_data or not orders_data.get('orders'):
            st.info("Aucun ordre ouvert trouvé")
            return
        
        orders = orders_data['orders']
        
        col1, col2, col3 = st.columns(3)
        
        # Statistiques des ordres
        total_orders = len(orders)
        buy_orders = len([o for o in orders if o.get('side') == 'BUY'])
        sell_orders = len([o for o in orders if o.get('side') == 'SELL'])
        
        col1.metric("📊 Total ordres", total_orders)
        col2.metric("🟢 Ordres d'achat", buy_orders)
        col3.metric("🔴 Ordres de vente", sell_orders)
        
        # DataFrame des ordres
        if orders:
            df_orders = pd.DataFrame(orders)
            display_cols = ['symbol', 'side', 'type', 'price', 'origQty', 'status']
            available_cols = [col for col in display_cols if col in df_orders.columns]
            
            st.dataframe(
                df_orders[available_cols],
                use_container_width=True
            )
    
    def display_sync_analysis(self, trades_data, bot_trades):
        """Analyse de synchronisation entre Binance et Firebase"""
        st.subheader("🔄 Analyse de Synchronisation")
        
        if not trades_data or not bot_trades:
            st.warning("⚠️ Données insuffisantes pour l'analyse de synchronisation")
            return
        
        binance_trades = trades_data.get('trades', [])
        
        # Analyse temporelle
        now = datetime.now()
        last_binance_sync = trades_data.get('timestamp', '')
        
        try:
            last_sync_time = datetime.fromisoformat(last_binance_sync)
            sync_delay = (now - last_sync_time).total_seconds() / 60  # en minutes
            
            col1, col2, col3 = st.columns(3)
            
            col1.metric("⏰ Dernière sync", f"{sync_delay:.1f} min")
            col2.metric("📊 Trades Binance", len(binance_trades))
            col3.metric("🤖 Trades Bot", len(bot_trades))
            
            # Indicateur de santé de la sync
            if sync_delay < 5:
                st.success("🟢 Synchronisation en temps réel")
            elif sync_delay < 15:
                st.warning("🟡 Léger délai de synchronisation")
            else:
                st.error("🔴 Délai de synchronisation important")
                
        except ValueError:
            st.error("❌ Erreur dans l'analyse temporelle")
    
    def run(self):
        """Interface principale de la page"""
        st.title("🔍 Comparaison Binance ↔ Firebase")
        st.markdown("Compare les données collectées en temps réel avec les trades du bot")
        
        # Récupération des données
        with st.spinner("📡 Récupération des données..."):
            account_data, trades_data, orders_data, health_data = self.get_binance_live_data()
            bot_trades = self.get_bot_trades_data()
        
        # Onglets pour organiser l'affichage
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Statut", "💼 Comptes", "🔄 Trades", "📋 Ordres"])
        
        with tab1:
            self.display_service_status(health_data)
            
            # Boutons d'action
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Actualiser les données"):
                    st.rerun()
            
            with col2:
                if st.button("📊 Vérifier le service"):
                    if health_data:
                        st.success("✅ Service binance-live opérationnel")
                    else:
                        st.error("❌ Service binance-live non détecté")
            
            with col3:
                if st.button("⚡ Forcer une collecte"):
                    st.info("🔄 Fonctionnalité à venir - Déclenchement manuel de collecte")
        
        with tab2:
            self.display_account_comparison(account_data)
        
        with tab3:
            self.display_trades_comparison(trades_data, bot_trades)
            self.display_sync_analysis(trades_data, bot_trades)
        
        with tab4:
            self.display_orders_comparison(orders_data)
        
        # Footer avec informations de debug
        with st.expander("🔧 Informations de debug"):
            st.write("**Données brutes (extrait):**")
            debug_data = {
                'health_status': health_data.get('status') if health_data else None,
                'account_balances_count': len(account_data.get('balances', [])) if account_data else 0,
                'binance_trades_count': len(trades_data.get('trades', [])) if trades_data else 0,
                'bot_trades_count': len(bot_trades),
                'open_orders_count': len(orders_data.get('orders', [])) if orders_data else 0
            }
            st.json(debug_data)


# Interface Streamlit
def main():
    st.set_page_config(
        page_title="Comparaison Binance/Firebase",
        page_icon="🔍",
        layout="wide"
    )
    
    comparison = BinanceFirebaseComparison()
    comparison.run()


if __name__ == "__main__":
    main()
>>>>>>> feature/clean-config
