import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_BASE = 'http://localhost:8000';

interface QuickInsight {
  metric: string;
  value: string;
  trend: string;
}

interface ChartConfig {
  type: string;
  title: string;
  data_key: string;
  x_field?: string;
  y_fields?: string[];
  name_field?: string;
  value_field?: string;
  description?: string;
}

interface AnalysisResult {
  analysis_id: string;
  query: string;
  status: string;
  results?: {
    data: any;
    analysis: string;
    recommendations: string;
    charts?: ChartConfig[];
  };
}

const colors = {
  primary: '#29b5e8',
  secondary: '#00d4ff',
  accent: '#8b5cf6',
  success: '#4ade80',
  warning: '#f59e0b',
  bg: '#0a0a0a',
  bgCard: '#111111',
  bgHover: '#1a1a1a',
  border: '#333333',
  text: '#e5e7eb',
  textMuted: '#9ca3af',
  gradient: 'linear-gradient(135deg, #29b5e8 0%, #00d4ff 100%)'
};

const CHART_COLORS = ['#29b5e8', '#8b5cf6', '#4ade80', '#f59e0b', '#00d4ff', '#fb923c'];

const truncateText = (text: string, maxLength: number = 20): string => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

function ChartRenderer({ config, data }: { config: ChartConfig; data: any }) {
  const chartData = data[config.data_key];
  
  if (!chartData) {
    console.error(`No data found for key: ${config.data_key}`);
    return null;
  }

  let dataArray = Array.isArray(chartData) ? chartData : chartData[Object.keys(chartData)[0]];
  
  if (!dataArray || dataArray.length === 0) {
    console.error(`Empty data array for: ${config.data_key}`);
    return null;
  }

  console.log(`Rendering ${config.type} chart with ${dataArray.length} items`);

  const displayData = dataArray.map((item: any) => {
    const newItem = { ...item };
    if (config.x_field && typeof newItem[config.x_field] === 'string') {
      newItem._original = newItem[config.x_field];
      newItem[config.x_field] = truncateText(newItem[config.x_field], 15);
    }
    if (config.name_field && typeof newItem[config.name_field] === 'string') {
      newItem._original_name = newItem[config.name_field];
      newItem[config.name_field] = truncateText(newItem[config.name_field], 15);
    }
    return newItem;
  });

  const renderChart = () => {
    switch (config.type) {
      case 'line':
      const currencyFields = config.y_fields?.filter(f => 
        f.toLowerCase().includes('revenue') || 
        f.toLowerCase().includes('price') || 
        f.toLowerCase().includes('amount')
      ) || [];
      const nonCurrencyFields = config.y_fields?.filter(f => !currencyFields.includes(f)) || [];
      const hasMixedScales = currencyFields.length > 0 && nonCurrencyFields.length > 0;

      return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={displayData}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
            <XAxis 
              dataKey={config.x_field} 
              stroke={colors.textMuted}
              style={{ fontSize: '11px' }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              yAxisId="left"
              stroke={colors.textMuted}
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => {
                if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
                return `$${Math.round(value)}`;
              }}
            />
            {hasMixedScales && (
              <YAxis 
                yAxisId="right"
                orientation="right"
                stroke={colors.textMuted}
                style={{ fontSize: '12px' }}
                tickFormatter={(value) => Math.round(value).toString()}
              />
            )}
            <Tooltip 
              contentStyle={{ 
                backgroundColor: colors.bgCard, 
                border: `1px solid ${colors.border}`,
                borderRadius: '8px',
                color: colors.text
              }}
              formatter={(value: any, name: string) => {
                const isCurrency = currencyFields.includes(name);
                if (typeof value === 'number') {
                  return isCurrency 
                    ? [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name]
                    : [value.toLocaleString(), name];
                }
                return [value, name];
              }}
            />
            <Legend />
            {config.y_fields?.map((field, idx) => {
              const isCurrency = currencyFields.includes(field);
              return (
                <Line 
                  key={field}
                  yAxisId={hasMixedScales && !isCurrency ? "right" : "left"}
                  type="monotone" 
                  dataKey={field} 
                  stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                  strokeWidth={2}
                  dot={{ fill: CHART_COLORS[idx % CHART_COLORS.length], r: 4 }}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      );

      case 'bar':
      const barHeight = Math.max(450, displayData.length * 60);
      
      const barNonCurrencyFields = config.y_fields?.filter(f => 
        f.toLowerCase().includes('count') ||
        f.toLowerCase().includes('orders') ||
        f.toLowerCase().includes('quantity') ||
        f.toLowerCase().includes('units') ||
        f.toLowerCase().includes('sold') ||
        f.toLowerCase().includes('items')
      ) || [];
      const barCurrencyFields = config.y_fields?.filter(f => !barNonCurrencyFields.includes(f)) || [];
      const barHasMixedScales = barCurrencyFields.length > 0 && barNonCurrencyFields.length > 0;
      return (
        <ResponsiveContainer width="100%" height={barHeight}>
          <BarChart 
            data={displayData}
            margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
            <XAxis 
              dataKey={config.x_field} 
              stroke={colors.textMuted}
              style={{ fontSize: '12px', fill: colors.text }}
              angle={-45}
              textAnchor="end"
              height={100}
              interval={0}
              tick={{ fill: colors.text }}
            />
            <YAxis 
              yAxisId="left"
              stroke={colors.textMuted}
              style={{ fontSize: '12px', fill: colors.text }}
              tick={{ fill: colors.text }}
              tickFormatter={(value) => {
                if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
                return `$${Math.round(value)}`;
              }}
            />
            {barHasMixedScales && (
              <YAxis 
                yAxisId="right"
                orientation="right"
                stroke={colors.textMuted}
                style={{ fontSize: '12px', fill: colors.text }}
                tick={{ fill: colors.text }}
                tickFormatter={(value) => Math.round(value).toString()}
              />
            )}
            <Tooltip 
              contentStyle={{ 
                backgroundColor: colors.bgCard, 
                border: `1px solid ${colors.border}`,
                borderRadius: '8px',
                color: colors.text
              }}
              formatter={(value: any, name: string, props: any) => {
                const originalName = props.payload._original || props.payload[config.x_field || ''];
                const isCurrency = barCurrencyFields.includes(name);
                if (typeof value === 'number') {
                  return isCurrency
                    ? [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name]
                    : [value.toLocaleString(), name];
                }
                return [value, originalName || name];
              }}
              labelFormatter={(label: any) => {
                const dataPoint = displayData.find((item: any) => item[config.x_field || ''] === label);
                return dataPoint?._original || label;
              }}
            />
            <Legend wrapperStyle={{ color: colors.text }} />
            {config.y_fields?.map((field, idx) => {
              const isCurrency = barCurrencyFields.includes(field);
              return (
                <Bar 
                  key={field}
                  yAxisId={barHasMixedScales && !isCurrency ? "right" : "left"}
                  dataKey={field} 
                  fill={CHART_COLORS[idx % CHART_COLORS.length]}
                  radius={[8, 8, 0, 0]}
                />
              );
            })}
          </BarChart>
        </ResponsiveContainer>
      );

      case 'horizontal_bar':
        const hBarHeight = Math.max(400, displayData.length * 60);
        return (
          <ResponsiveContainer width="100%" height={hBarHeight}>
            <BarChart 
              data={displayData} 
              layout="vertical"
              margin={{ top: 20, right: 80, left: 220, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
              <XAxis 
                type="number"
                stroke={colors.text}
                tick={{ fill: colors.text, fontSize: 12 }}
                tickFormatter={(value) => {
                  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
                  return `$${Math.round(value)}`;
                }}
              />
              <YAxis 
                type="category"
                dataKey={config.x_field}
                stroke={colors.text}
                width={270}
                interval={0}
                tick={(props: any) => {
                  const { x, y, payload } = props;
                  if (!payload || !payload.value) {
                    return <g />;
                  }
                  
                  const dataPoint = displayData.find((item: any) => 
                    item[config.x_field || ''] === payload.value
                  );
                  const fullText = dataPoint?._original || payload.value || '';
                  const displayText = truncateText(String(fullText), 40);
                  
                  return (
                    <g transform={`translate(${x},${y})`}>
                      <text 
                        x={-10} 
                        y={0} 
                        dy={4} 
                        textAnchor="end" 
                        fill={colors.text}
                        fontSize={11}
                        fontFamily="Inter, system-ui, sans-serif"
                      >
                        {displayText}
                      </text>
                    </g>
                  );
                }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: colors.bgCard, 
                  border: `1px solid ${colors.border}`,
                  borderRadius: '8px',
                  color: colors.text
                }}
                formatter={(value: any, name: string) => {
                  if (typeof value === 'number') {
                    return [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name];
                  }
                  return [value, name];
                }}
                labelFormatter={(label: any) => {
                  const dataPoint = displayData.find((item: any) => 
                    item[config.x_field || ''] === label
                  );
                  return dataPoint?._original || label;
                }}
              />
              <Legend wrapperStyle={{ color: colors.text }} />
              {config.y_fields?.map((field, idx) => (
                <Bar 
                  key={field}
                  dataKey={field}
                  fill={CHART_COLORS[idx % CHART_COLORS.length]}
                  radius={[0, 8, 8, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'pie':
        if (!config.value_field || !config.name_field) return null;
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={displayData}
                dataKey={config.value_field}
                nameKey={config.name_field}
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry: any) => {
                  const name = entry._original_name || entry[config.name_field || 'name'];
                  return truncateText(name, 12);
                }}
              >
                {displayData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: colors.bgCard, 
                  border: `1px solid ${colors.border}`,
                  borderRadius: '8px',
                  color: colors.text
                }}
                formatter={(value: any, name: string) => {
                  if (typeof value === 'number') {
                    return [`$${value.toLocaleString()}`, name];
                  }
                  return [value, name];
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return <div style={{ color: colors.textMuted }}>Unsupported chart type: {config.type}</div>;
    }
  };

  return (
    <div style={{ 
      background: colors.bgCard,
      border: `1px solid ${colors.border}`,
      borderRadius: '12px',
      padding: '24px',
      marginBottom: '24px'
    }}>
      <div style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '16px',
        fontWeight: '600',
        marginBottom: '8px',
        color: colors.text
      }}>
        {config.title}
      </div>
      {config.description && (
        <div style={{
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize: '13px',
          color: colors.textMuted,
          marginBottom: '20px'
        }}>
          {config.description}
        </div>
      )}
      {renderChart()}
    </div>
  );
}

function QuickInsights() {
  const [insights, setInsights] = useState<QuickInsight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/quick-insights`)
      .then(response => response.json())
      .then(data => {
        setInsights(data.insights);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching insights:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: colors.text }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: `3px solid ${colors.border}`,
          borderTop: `3px solid ${colors.primary}`,
          borderRadius: '50%',
          margin: '0 auto 20px',
          animation: 'spin 1s linear infinite'
        }}></div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '16px' }}>
          LOADING INSIGHTS...
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
      {insights.map((insight, index) => (
        <div key={index} style={{ 
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: '12px',
          padding: '24px',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.3s ease',
          cursor: 'pointer'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.borderColor = colors.primary;
          e.currentTarget.style.boxShadow = `0 10px 40px rgba(41, 181, 232, 0.2)`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.borderColor = colors.border;
          e.currentTarget.style.boxShadow = 'none';
        }}>
          <div style={{
            position: 'absolute',
            top: '0',
            left: '0',
            right: '0',
            height: '3px',
            background: colors.gradient
          }}></div>
          <div style={{ 
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12px', 
            color: colors.textMuted,
            marginBottom: '12px',
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}>
            {insight.metric}
          </div>
          <div style={{ 
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '28px', 
            fontWeight: '700',
            marginBottom: '8px',
            color: colors.text,
            background: colors.gradient,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            {insight.value}
          </div>
          <div style={{ 
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '13px', 
            color: colors.success,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span>▲</span> {insight.trend}
          </div>
        </div>
      ))}
    </div>
  );
}

function AnalysisChat() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query })
      });
      
      if (!response.ok) throw new Error('Failed to analyze');
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Failed to analyze data. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ 
        background: colors.bgCard,
        border: `1px solid ${colors.border}`,
        borderRadius: '12px',
        padding: '24px'
      }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <input
              type="text"
              placeholder="Ask about your e-commerce data..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              style={{
                width: '100%',
                padding: '16px 20px',
                background: colors.bg,
                border: `2px solid ${colors.border}`,
                borderRadius: '8px',
                fontSize: '16px',
                fontFamily: 'JetBrains Mono, monospace',
                color: colors.text,
                outline: 'none',
                transition: 'border-color 0.3s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = colors.primary}
              onBlur={(e) => e.target.style.borderColor = colors.border}
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={loading}
            style={{
              padding: '16px 32px',
              background: loading ? colors.textMuted : colors.gradient,
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontFamily: 'JetBrains Mono, monospace',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.transform = 'scale(1.05)';
                e.currentTarget.style.boxShadow = `0 8px 25px rgba(41, 181, 232, 0.4)`;
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            {loading ? 'ANALYZING...' : 'ANALYZE'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '16px 20px',
          background: `rgba(239, 68, 68, 0.1)`,
          border: `1px solid rgba(239, 68, 68, 0.3)`,
          borderRadius: '8px',
          color: '#ef4444',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '14px'
        }}>
          ⚠ {error}
        </div>
      )}

      {result && result.results && (
        <div>
          <div style={{
            background: colors.bgCard,
            border: `1px solid ${colors.border}`,
            borderRadius: '12px',
            overflow: 'hidden',
            marginBottom: '24px'
          }}>
            <div style={{
              background: colors.gradient,
              padding: '16px 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '14px',
                fontWeight: '600',
                color: 'white'
              }}>
                QUERY: {result.query}
              </div>
              <span style={{
                padding: '4px 12px',
                background: 'rgba(255,255,255,0.2)',
                borderRadius: '20px',
                fontSize: '11px',
                fontFamily: 'JetBrains Mono, monospace',
                color: 'white'
              }}>
                {result.status}
              </span>
            </div>

            <div style={{ padding: '24px' }}>
              <div style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                fontWeight: '600',
                marginBottom: '12px',
                color: colors.primary,
                textTransform: 'uppercase',
                letterSpacing: '1px'
              }}>
                ▸ ANALYSIS
              </div>
              <div 
                style={{ 
                  fontFamily: 'Inter, system-ui, sans-serif',
                  fontSize: '15px',
                  lineHeight: '1.6',
                  color: colors.text,
                  background: colors.bg,
                  padding: '20px',
                  borderRadius: '8px',
                  border: `1px solid ${colors.border}`,
                  marginBottom: '24px'
                }}
                dangerouslySetInnerHTML={{ 
                  __html: result.results.analysis
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br />')
                }}
              />

              <div style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                fontWeight: '600',
                marginBottom: '12px',
                color: colors.secondary,
                textTransform: 'uppercase',
                letterSpacing: '1px'
              }}>
                ▸ RECOMMENDATIONS
              </div>
              <div 
                style={{ 
                  fontFamily: 'Inter, system-ui, sans-serif',
                  fontSize: '15px',
                  lineHeight: '1.6',
                  color: colors.text,
                  background: colors.bg,
                  padding: '20px',
                  borderRadius: '8px',
                  border: `1px solid ${colors.border}`
                }}
                dangerouslySetInnerHTML={{ 
                  __html: result.results.recommendations
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br />')
                }}
              />
            </div>
          </div>

          {result.results.charts && result.results.charts.length > 0 && (
            <div>
              <div style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '18px',
                fontWeight: '600',
                marginBottom: '20px',
                color: colors.text,
                textTransform: 'uppercase',
                letterSpacing: '1px'
              }}>
                VISUALIZATIONS ({result.results.charts.length})
              </div>
              {result.results.charts.map((chart, idx) => (
                <ChartRenderer key={idx} config={chart} data={result.results!.data} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState('insights');

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        body {
          margin: 0;
          background: ${colors.bg};
          font-family: 'Inter', system-ui, sans-serif;
          color: ${colors.text};
          overflow-x: hidden;
        }
        
        * {
          box-sizing: border-box;
        }
        
        ::-webkit-scrollbar {
          width: 8px;
        }
        
        ::-webkit-scrollbar-track {
          background: ${colors.bg};
        }
        
        ::-webkit-scrollbar-thumb {
          background: ${colors.border};
          border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: ${colors.primary};
        }
      `}</style>
      
      <div style={{ 
        minHeight: '100vh',
        background: colors.bg,
        position: 'relative'
      }}>
        <div style={{
          position: 'fixed',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: `radial-gradient(circle at 25% 25%, rgba(41, 181, 232, 0.1) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(0, 212, 255, 0.05) 0%, transparent 50%)`,
          pointerEvents: 'none',
          zIndex: 0
        }}></div>
        
        <div style={{ 
          maxWidth: '1400px', 
          margin: '0 auto', 
          padding: '40px 24px',
          position: 'relative',
          zIndex: 1
        }}>
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <h1 style={{ 
              fontSize: '48px', 
              fontWeight: '700',
              marginBottom: '16px',
              fontFamily: 'JetBrains Mono, monospace',
              background: colors.gradient,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '-1px'
            }}>
              E-COMMERCE AI ANALYZER
            </h1>
            <p style={{ 
              color: colors.textMuted,
              fontSize: '18px',
              fontFamily: 'Inter, system-ui, sans-serif',
              fontWeight: '400',
              maxWidth: '600px',
              margin: '0 auto'
            }}>
              AI-powered insights with interactive visualizations from your Snowflake data
            </p>
          </div>

          <div style={{ 
            marginBottom: '40px',
            display: 'flex',
            justifyContent: 'center'
          }}>
            <div style={{ 
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: '12px',
              padding: '6px',
              display: 'flex'
            }}>
              <button
                onClick={() => setActiveTab('insights')}
                style={{
                  padding: '12px 32px',
                  border: 'none',
                  backgroundColor: activeTab === 'insights' ? colors.primary : 'transparent',
                  color: activeTab === 'insights' ? 'white' : colors.textMuted,
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  borderRadius: '8px',
                  transition: 'all 0.3s ease'
                }}
              >
                QUICK INSIGHTS
              </button>
              <button
                onClick={() => setActiveTab('analysis')}
                style={{
                  padding: '12px 32px',
                  border: 'none',
                  backgroundColor: activeTab === 'analysis' ? colors.primary : 'transparent',
                  color: activeTab === 'analysis' ? 'white' : colors.textMuted,
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  borderRadius: '8px',
                  transition: 'all 0.3s ease'
                }}
              >
                AI ANALYSIS
              </button>
            </div>
          </div>

          <div>
            {activeTab === 'insights' && <QuickInsights />}
            {activeTab === 'analysis' && <AnalysisChat />}
          </div>
        </div>
      </div>
    </>
  );
}

export default App;