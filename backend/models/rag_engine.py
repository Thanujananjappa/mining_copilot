from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from utils.langchain_setup import langchain_setup
from utils.chromadb_manager import ChromaDBManager
from database.db_config import get_mysql_connection
from models.mistral_client import MistralService
from config import Config
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.chroma_manager = ChromaDBManager()
        self.mistral = MistralService()
        # ✅ ADDED: Initialize LangChain prompt and components
        self.prompt = langchain_setup.create_custom_prompt()
        
    def query(self, question, language='en'):
        """
        Returns structured response for chat interface
        """
        try:
            # 1. Vector Search + SQL Context + AI Answer (existing code)
            relevant_docs = self.chroma_manager.similarity_search(question, k=Config.TOP_K_RESULTS)
            sql_context = self.get_sql_context(question)
            vector_context = "\n\n".join([doc.page_content for doc in relevant_docs])
            full_context = f"{vector_context}\n\nDatabase Records:\n{sql_context}"
            answer = self.mistral.generate_response(full_context, question)
            
            # 2. Get Enhanced Visualization Data
            viz_data = self.get_enhanced_visualization_data(question)
            
            # 3. Generate Manager Recommendations
            recommendations = self.generate_recommendations(question, answer, viz_data)
            
            return {
                "answer": answer,
                "type": "ai_response",  # ✅ Identify response type
                "visualizations": {
                    "kpis": viz_data["kpis"],
                    "charts": self.filter_relevant_charts(question, viz_data["charts"]),
                    "tables": self.extract_data_tables(question, sql_context)
                },
                "recommendations": recommendations,
                "sources": [doc.metadata for doc in relevant_docs],
                "language": language
            }
        except Exception as e:
            logger.error(f"❌ RAG query error: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "type": "error",
                "visualizations": {},
                "recommendations": [],
                "sources": [],
                "language": language
            }

    def generate_recommendations(self, question, answer, viz_data):
        """Generate actionable recommendations for managers"""
        recommendations = []
        
        # Analyze question context for specific recommendations
        query_lower = question.lower()
        
        if any(word in query_lower for word in ['equipment', 'machine', 'status']):
            critical_count = viz_data["kpis"].get("critical_alerts", 0)
            if critical_count > 0:
                recommendations.append(f"🚨 Immediate attention needed for {critical_count} critical equipment")
                recommendations.append("Schedule maintenance for equipment with efficiency below 70%")
                recommendations.append("Review equipment alerts in the maintenance dashboard")
        
        if any(word in query_lower for word in ['production', 'output', 'efficiency']):
            efficiency = viz_data["kpis"].get("avg_efficiency", 0)
            if efficiency < 80:
                recommendations.append(f"📊 Production efficiency ({efficiency}%) below target - investigate bottlenecks")
                recommendations.append("Optimize shift schedules to improve equipment utilization")
            else:
                recommendations.append(f"✅ Good production efficiency ({efficiency}%) - maintain current processes")
        
        if any(word in query_lower for word in ['safety', 'incident', 'accident']):
            incidents = viz_data["kpis"].get("total_incidents", 0)
            if incidents > 0:
                recommendations.append(f"⚠️ {incidents} safety incidents reported - review safety protocols")
                recommendations.append("Conduct safety audit in high-risk areas")
            else:
                recommendations.append("✅ No recent safety incidents - continue current safety measures")
        
        # Always add general recommendations
        if not recommendations:
            recommendations = [
                "Review weekly equipment maintenance schedules",
                "Monitor production targets vs actual performance", 
                "Check safety compliance reports regularly",
                "Optimize fuel consumption across all sites"
            ]
        
        return recommendations[:4]  # Return top 4 recommendations

    def filter_relevant_charts(self, question, charts_data):
        """Return only charts relevant to the question"""
        query_lower = question.lower()
        relevant_charts = {}
        
        if any(word in query_lower for word in ['trend', 'history', 'over time']):
            if "incidents_trend" in charts_data:
                relevant_charts["incidents_trend"] = charts_data["incidents_trend"]
            if "production_metrics" in charts_data:
                relevant_charts["production_trend"] = charts_data["production_metrics"]
        
        if any(word in query_lower for word in ['equipment', 'machine', 'status']):
            if "equipment_status" in charts_data:
                relevant_charts["equipment_status"] = charts_data["equipment_status"]
        
        if any(word in query_lower for word in ['production', 'output', 'efficiency']):
            if "production_metrics" in charts_data:
                relevant_charts["production_trend"] = charts_data["production_metrics"]
        
        return relevant_charts

    def extract_data_tables(self, question, sql_context):
        """Extract structured data tables from SQL context"""
        # This would parse the SQL response into table format
        # For now, return simplified version
        return {
            "summary": f"Data from {len(sql_context.splitlines())} records",
            "preview": sql_context[:200] + "..." if len(sql_context) > 200 else sql_context
        }

    def get_enhanced_visualization_data(self, query):
        """Get enhanced visualization data with additional charts"""
        try:
            conn = get_mysql_connection()
            
            viz_data = {
                "kpis": self.get_kpis(conn),
                "charts": {
                    "incidents_trend": self.get_incidents_trend(conn),
                    "equipment_status": self.get_equipment_status(conn),
                    "production_metrics": self.get_production_trend(conn),
                    "efficiency_trend": self.get_efficiency_trend(conn)
                }
            }
            
            conn.close()
            return viz_data
        except Exception as e:
            logger.error(f"❌ Enhanced visualization data error: {e}")
            return {"kpis": {}, "charts": {}}

    def get_efficiency_trend(self, conn):
        """Get efficiency trend data"""
        try:
            query = """
                SELECT 
                    DATE_FORMAT(metric_date, '%Y-%m') as month,
                    AVG(efficiency_percentage) as avg_efficiency
                FROM production_metrics
                WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY month
                ORDER BY month DESC
            """
            return pd.read_sql(query, conn).to_dict(orient='records')
        except Exception as e:
            logger.error(f"❌ Efficiency trend error: {e}")
            return []

    def get_sql_context(self, query):
        """Fetch relevant MySQL data with enhanced query routing"""
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        query_lower = query.lower()
        
        try:
            # Enhanced query routing with multiple conditions
            if any(word in query_lower for word in ['incident', 'accident', 'safety', 'casualt', 'injur']):
                cursor.execute("""
                    SELECT 
                        incident_date, 
                        mine_name, 
                        incident_type, 
                        severity, 
                        description, 
                        casualties,
                        injuries,
                        cost_impact,
                        response_time_minutes
                    FROM mining_incidents 
                    WHERE incident_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                    ORDER BY 
                        CASE severity 
                            WHEN 'Critical' THEN 4
                            WHEN 'High' THEN 3
                            WHEN 'Medium' THEN 2
                            ELSE 1 
                        END DESC,
                        incident_date DESC 
                    LIMIT 8
                """)
                
            elif any(word in query_lower for word in ['equipment', 'machine', 'maintenance', 'repair', 'breakdown']):
                # Check if query is about maintenance history or current status
                if any(word in query_lower for word in ['history', 'past', 'last', 'previous']):
                    cursor.execute("""
                        SELECT 
                            mr.equipment_id,
                            mr.maintenance_type,
                            mr.start_date,
                            mr.end_date,
                            mr.cost,
                            mr.downtime_hours,
                            em.equipment_type
                        FROM maintenance_repairs mr
                        LEFT JOIN equipment_monitoring em ON mr.equipment_id = em.equipment_id
                        ORDER BY mr.start_date DESC 
                        LIMIT 6
                    """)
                else:
                    cursor.execute("""
                        SELECT 
                            equipment_id, 
                            equipment_type, 
                            status, 
                            efficiency_score, 
                            alerts,
                            temperature_celsius,
                            vibration_level,
                            last_maintenance,
                            next_maintenance
                        FROM equipment_monitoring 
                        WHERE status != 'Operational' OR efficiency_score < 80
                        ORDER BY 
                            CASE status 
                                WHEN 'Critical' THEN 4
                                WHEN 'Maintenance' THEN 3
                                WHEN 'Offline' THEN 2
                                ELSE 1 
                            END DESC,
                            efficiency_score ASC 
                        LIMIT 8
                    """)
                    
            elif any(word in query_lower for word in ['production', 'output', 'tons', 'efficiency', 'downtime']):
                cursor.execute("""
                    SELECT 
                        metric_date, 
                        site_name, 
                        material_type, 
                        quantity_tons, 
                        efficiency_percentage,
                        downtime_hours,
                        target_tons,
                        cost_per_ton
                    FROM production_metrics 
                    WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    ORDER BY metric_date DESC, quantity_tons DESC 
                    LIMIT 8
                """)
                
            elif any(word in query_lower for word in ['fuel', 'energy', 'consumption', 'power']):
                cursor.execute("""
                    SELECT 
                        equipment_id,
                        reading_date,
                        fuel_liters,
                        energy_kwh,
                        shift
                    FROM fuel_energy 
                    WHERE reading_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ORDER BY reading_date DESC, energy_kwh DESC 
                    LIMIT 6
                """)
                
            elif any(word in query_lower for word in ['quality', 'defect', 'grade', 'inspection']):
                cursor.execute("""
                    SELECT 
                        site_name,
                        metric_date,
                        material_type,
                        quality_grade,
                        defects_found
                    FROM quality_metrics 
                    WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    ORDER BY metric_date DESC, defects_found DESC 
                    LIMIT 6
                """)
                
            elif any(word in query_lower for word in ['safety', 'compliance', 'audit', 'violation']):
                cursor.execute("""
                    SELECT 
                        audit_date,
                        site_name,
                        compliance_score,
                        violations,
                        auditor_name,
                        recommendations
                    FROM safety_compliance 
                    ORDER BY audit_date DESC 
                    LIMIT 5
                """)
                
            else:
                # Default: mixed context from multiple tables
                cursor.execute("""
                    (SELECT 
                        'incident' as source_type,
                        incident_date as date,
                        mine_name as name,
                        severity as metric,
                        description as details
                    FROM mining_incidents 
                    ORDER BY incident_date DESC 
                    LIMIT 2)
                    
                    UNION ALL
                    
                    (SELECT 
                        'equipment' as source_type,
                        updated_at as date,
                        equipment_id as name,
                        status as metric,
                        alerts as details
                    FROM equipment_monitoring 
                    WHERE status != 'Operational'
                    ORDER BY updated_at DESC 
                    LIMIT 2)
                    
                    UNION ALL
                    
                    (SELECT 
                        'production' as source_type,
                        metric_date as date,
                        site_name as name,
                        efficiency_percentage as metric,
                        CONCAT('Production: ', quantity_tons, ' tons') as details
                    FROM production_metrics 
                    ORDER BY metric_date DESC 
                    LIMIT 2)
                    
                    ORDER BY date DESC
                """)
            
            results = cursor.fetchall()
            
            # Format results for better readability
            if results:
                df = pd.DataFrame(results)
                
                # Add context summary
                summary = f"Retrieved {len(results)} records from database.\n\n"
                
                return summary + df.to_string(index=False, max_colwidth=50)
            else:
                return "No relevant data found in database for this query."
                
        except Exception as e:
            logger.error(f"❌ SQL context error: {e}")
            return f"Database query error: {str(e)}"
        
        finally:
            cursor.close()
            conn.close()
    
    def get_visualization_data(self, query):
        """Get data for charts and KPIs"""
        try:
            conn = get_mysql_connection()
            
            viz_data = {
                "kpis": self.get_kpis(conn),
                "charts": {
                    "incidents_trend": self.get_incidents_trend(conn),
                    "equipment_status": self.get_equipment_status(conn),
                    "production_metrics": self.get_production_trend(conn)
                }
            }
            
            conn.close()
            return viz_data
        except Exception as e:
            logger.error(f"❌ Visualization data error: {e}")
            return {"kpis": {}, "charts": {}}
    
    def get_kpis(self, conn):
        """Calculate KPIs"""
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Total incidents
            cursor.execute("SELECT COUNT(*) as total_incidents FROM mining_incidents")
            total_incidents = cursor.fetchone()['total_incidents']
            
            # Critical alerts
            cursor.execute("SELECT COUNT(*) as critical_alerts FROM equipment_monitoring WHERE status='Critical'")
            critical_alerts = cursor.fetchone()['critical_alerts']
            
            # Average efficiency
            cursor.execute("SELECT AVG(efficiency_percentage) as avg_efficiency FROM production_metrics WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
            avg_efficiency = cursor.fetchone()['avg_efficiency'] or 0
            
            # Monthly production
            cursor.execute("SELECT SUM(quantity_tons) as monthly_production FROM production_metrics WHERE MONTH(metric_date) = MONTH(CURDATE())")
            monthly_production = cursor.fetchone()['monthly_production'] or 0
            
            cursor.close()
            
            return {
                "total_incidents": total_incidents,
                "critical_alerts": critical_alerts,
                "avg_efficiency": round(float(avg_efficiency), 2),
                "monthly_production": float(monthly_production)
            }
        except Exception as e:
            logger.error(f"❌ KPI calculation error: {e}")
            return {
                "total_incidents": 0,
                "critical_alerts": 0,
                "avg_efficiency": 0,
                "monthly_production": 0
            }
    
    def get_incidents_trend(self, conn):
        """Get incident trend data"""
        try:
            query = """
                SELECT 
                    DATE_FORMAT(incident_date, '%Y-%m') as month,
                    severity,
                    COUNT(*) as count
                FROM mining_incidents
                WHERE incident_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY month, severity
                ORDER BY month DESC
            """
            return pd.read_sql(query, conn).to_dict(orient='records')
        except Exception as e:
            logger.error(f"❌ Incidents trend error: {e}")
            return []
    
    def get_equipment_status(self, conn):
        """Get equipment status distribution"""
        try:
            query = """
                SELECT status, COUNT(*) as count
                FROM equipment_monitoring
                GROUP BY status
            """
            return pd.read_sql(query, conn).to_dict(orient='records')
        except Exception as e:
            logger.error(f"❌ Equipment status error: {e}")
            return []
    
    def get_production_trend(self, conn):
        """Get production trend"""
        try:
            query = """
                SELECT 
                    DATE_FORMAT(metric_date, '%Y-%m') as month,
                    SUM(quantity_tons) as production,
                    AVG(efficiency_percentage) as efficiency
                FROM production_metrics
                WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY month
                ORDER BY month DESC
            """
            return pd.read_sql(query, conn).to_dict(orient='records')
        except Exception as e:
            logger.error(f"❌ Production trend error: {e}")
            return []