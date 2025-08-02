#!/usr/bin/env python3
"""
🔍 PAGE COMPARAISON BINANCE/FIREBASE
Compare les données collectées par le service binance-live avec Firebase
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
import json

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from firebase_config import StreamlitFirebaseConfig
    from config import APIConfig
except ImportError as e:
    st.error(f"❌ Erreur import: {e}")
    st.stop()


class BinanceFirebaseComparison:
    """Classe pour comparer les données Binance/Firebase"""
    
    def __init__(self):
        self.firebase_config = None
        self.setup_firebase()
        
    def setup_firebase(self):
        """Configuration Firebase"""
        try:
            self.firebase_config = StreamlitFirebaseConfig()
            st.success("🔥 Firebase connecté avec succès")
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
    
    def get_binance_live_data(self):
        """Récupère les données Firebase avec les nouvelles collections"""
        try:
            if not self.firebase_config:
                return None, None, None, None
            
            # Utiliser les vraies collections du bot
            trades_data = self.firebase_config.get_trades_data(limit=50)
            positions_data = self.firebase_config.get_positions_data()
            health_data = self.firebase_config.get_bot_health()
            
            # Simuler account_data basé sur les trades
            total_pnl = sum([t.get('pnl_usdc', 0) for t in trades_data if isinstance(t.get('pnl_usdc'), (int, float))])
            account_data = {
                'total_value_usdc_approx': 1000 + total_pnl,  # Capital de base + P&L
                'free_usdc': max(0, 1000 + total_pnl - len(positions_data) * 50),  # Approximation
                'timestamp': datetime.now().isoformat()
            }
            
            return account_data, trades_data, positions_data, health_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération données Firebase: {e}")
            return None, None, None, None
    
    def get_bot_trades_data(self):
        """Récupère les données des trades du bot principal"""
        try:
            if not self.firebase_config:
                return []
            
            # Utiliser la méthode standardisée
            return self.firebase_config.get_trades_data(limit=100)
            
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
