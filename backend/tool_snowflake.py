import json
import pandas as pd
import snowflake.connector
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class SnowflakeTools:
    def __init__(self):
        self.conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_RAW_SCHEMA'),
            role=os.getenv('SNOWFLAKE_ROLE'),
            insecure_mode=True,
        )
    
    def get_sales_metrics(self, days: int = 30) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM orders 
        WHERE order_date >= %s AND order_date <= %s
        """
        
        cursor.execute(query, (start_date, end_date))
        result = cursor.fetchone()
        
        return {
            "period_days": days,
            "total_orders": result[0] or 0,
            "total_revenue": float(result[1] or 0),
            "avg_order_value": float(result[2] or 0),
            "unique_customers": result[3] or 0
        }
    
    def get_top_products(self, limit: int = 10) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            p.product_name,
            SUM(oi.quantity) as total_sold,
            SUM(oi.total_price) as total_revenue,
            COUNT(DISTINCT oi.order_id) as orders_count
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY total_revenue DESC
        LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        products = []
        for row in results:
            products.append({
                "product_name": row[0],
                "total_sold": row[1],
                "total_revenue": float(row[2]),
                "orders_count": row[3]
            })
        
        return {"top_products": products}
    
    def get_customer_segments(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            CASE 
                WHEN annual_income >= 80000 THEN 'High Value'
                WHEN annual_income >= 50000 THEN 'Mid Value'
                ELSE 'Low Value'
            END as segment,
            COUNT(*) as customer_count,
            AVG(annual_income) as avg_income
        FROM customers
        WHERE is_active = TRUE
        GROUP BY segment
        ORDER BY avg_income DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        segments = []
        for row in results:
            segments.append({
                "segment": row[0],
                "customer_count": row[1],
                "avg_income": float(row[2])
            })
        
        return {"customer_segments": segments}
    
    def get_sales_trend(self, days: int = 30) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            DATE(order_date) as date,
            SUM(total_amount) as revenue,
            COUNT(*) as orders
        FROM orders 
        WHERE order_date >= %s AND order_date <= %s
        GROUP BY DATE(order_date)
        ORDER BY date
        """
        
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        
        trend_data = []
        for row in results:
            trend_data.append({
                "date": row[0].strftime('%Y-%m-%d'),
                "revenue": float(row[1]),
                "orders": row[2]
            })
        
        return {"sales_trend": trend_data}
    
    def get_revenue_by_category(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            CASE 
                WHEN p.product_name LIKE '%Pro%' THEN 'Pro'
                WHEN p.product_name LIKE '%Premium%' THEN 'Premium'
                WHEN p.product_name LIKE '%Standard%' THEN 'Standard'
                WHEN p.product_name LIKE '%Lite%' THEN 'Lite'
                WHEN p.product_name LIKE '%Ultra%' THEN 'Ultra'
                ELSE 'Other'
            END as category,
            SUM(oi.total_price) as revenue,
            COUNT(DISTINCT oi.order_id) as orders
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY category
        ORDER BY revenue DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        categories = []
        for row in results:
            categories.append({
                "category": row[0],
                "revenue": float(row[1]),
                "orders": row[2]
            })
        
        return {"revenue_by_category": categories}
    
    def get_monthly_comparison(self, months: int = 6) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            YEAR(order_date::DATE) || '-' || LPAD(MONTH(order_date::DATE), 2, '0') as month,
            SUM(total_amount) as revenue,
            COUNT(*) as orders,
            AVG(total_amount) as avg_order_value
        FROM orders 
        WHERE order_date::DATE >= DATEADD(month, -%s, CURRENT_DATE())
        GROUP BY YEAR(order_date::DATE), MONTH(order_date::DATE)
        ORDER BY YEAR(order_date::DATE), MONTH(order_date::DATE)
        """
        
        cursor.execute(query, (months,))
        results = cursor.fetchall()
        
        monthly_data = []
        for row in results:
            monthly_data.append({
                "month": row[0],
                "revenue": float(row[1]),
                "orders": row[2],
                "avg_order_value": float(row[3])
            })
        
        return {"monthly_comparison": monthly_data}
    
    def get_customer_lifetime_value(self, limit: int = 10) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            c.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(o.total_amount) as lifetime_value,
            AVG(o.total_amount) as avg_order_value
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, customer_name
        ORDER BY lifetime_value DESC
        LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        customers = []
        for row in results:
            customers.append({
                "customer_id": row[0],
                "customer_name": row[1],
                "total_orders": row[2],
                "lifetime_value": float(row[3]),
                "avg_order_value": float(row[4])
            })
        
        return {"top_customers": customers}