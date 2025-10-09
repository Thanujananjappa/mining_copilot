// Build timestamp: 2025-10-07-15:03
import { Component, Input, OnChanges, SimpleChanges, OnInit, OnDestroy } from '@angular/core';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-charts',
  templateUrl: './charts.component.html',
  styleUrls: ['./charts.component.css']
})
export class ChartsComponent implements OnInit, OnChanges, OnDestroy {
  @Input() data: any[] = [];
  @Input() type: 'line' | 'bar' | 'pie' | 'doughnut' = 'line';
  @Input() title: string = '';
  @Input() chartId: string = '';
  @Input() fuelChartData: any;
  @Input() productionChartData: any;

  chartInstance: Chart | null = null;
  private renderTimeout: any;

  /** Docker-safe method for canvas ID */
  getSafeChartId(): string {
    const baseId = this.chartId || this.title || 'chart';
    return baseId.replace(/[^a-zA-Z0-9]/g, '_') + '_chart';
  }

  ngOnInit(): void {
    if (this.data?.length) {
      this.safeRender();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['data'] || changes['type']) && this.data?.length) {
      this.safeRender();
    }
  }

  ngOnDestroy(): void {
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
    if (this.renderTimeout) {
      clearTimeout(this.renderTimeout);
    }
  }

  private safeRender() {
    if (this.renderTimeout) clearTimeout(this.renderTimeout);
    this.renderTimeout = setTimeout(() => this.renderChart(), 150);
  }

  private renderChart() {
    const canvas = document.getElementById(this.getSafeChartId()) as HTMLCanvasElement;
    if (!canvas) {
      console.warn('Canvas element not found for:', this.getSafeChartId());
      return;
    }

    if (this.chartInstance) this.chartInstance.destroy();
    const existingChart = Chart.getChart(canvas);
    if (existingChart) existingChart.destroy();

    let labels: string[] = [];
    let datasets: any[] = [];

    if (this.type === 'pie' || this.type === 'doughnut') {
      labels = this.data.map(d => d.status || d.type || d.name || d.label || 'Unknown');
      datasets = [{
        data: this.data.map(d => d.count || d.value || d.percentage || 0),
        backgroundColor: this.generateColors(labels.length, 0.7),
        borderColor: this.generateColors(labels.length, 1),
        borderWidth: 2
      }];
    } else {
      labels = Array.from(new Set(this.data.map(d => d.month || d.date || d.period || ''))).filter(Boolean);
      const numericFields = Object.keys(this.data[0] || {}).filter(k =>
        !['month', 'date', 'period', 'label', 'name', 'type'].includes(k)
      );

      datasets = numericFields.map((key, idx) => ({
        label: this.formatLabel(key),
        data: this.data.map(d => d[key] || 0),
        borderColor: this.getColor(idx),
        backgroundColor: this.type === 'bar' ? this.getColor(idx, 0.7) : this.getColor(idx, 0.1),
        fill: this.type === 'line',
        tension: 0.3,
        borderWidth: 2
      }));
    }

    this.chartInstance = new Chart(canvas, {
      type: this.type,
      data: { labels, datasets },
      options: this.getChartOptions()
    });

    setTimeout(() => this.chartInstance?.resize(), 100);
  }

  private getChartOptions(): any {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'top' as const },
        title: { display: !!this.title, text: this.title, font: { size: 14 } }
      }
    };

    if (this.type === 'line' || this.type === 'bar') {
      return {
        ...baseOptions,
        scales: {
          y: { beginAtZero: true },
          x: { ticks: { autoSkip: false, maxRotation: 45, minRotation: 0 } }
        }
      };
    }

    return baseOptions;
  }

  private generateColors(count: number, alpha: number = 1): string[] {
    const baseColors = [
      `rgba(76, 175, 80, ${alpha})`,
      `rgba(33, 150, 243, ${alpha})`,
      `rgba(255, 193, 7, ${alpha})`,
      `rgba(244, 67, 54, ${alpha})`,
      `rgba(156, 39, 176, ${alpha})`,
      `rgba(0, 188, 212, ${alpha})`,
      `rgba(255, 152, 0, ${alpha})`,
      `rgba(121, 85, 72, ${alpha})`
    ];

    if (count > baseColors.length) {
      const extraColors = [];
      for (let i = baseColors.length; i < count; i++) {
        const hue = (i * 137.508) % 360;
        extraColors.push(`hsla(${hue}, 70%, 65%, ${alpha})`);
      }
      return [...baseColors, ...extraColors].slice(0, count);
    }

    return baseColors.slice(0, count);
  }

  private formatLabel(key: string): string {
    return key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
  }

  private getColor(index: number, alpha = 1): string {
    const colors = [
      `rgba(76, 175, 80, ${alpha})`,
      `rgba(33, 150, 243, ${alpha})`,
      `rgba(255, 193, 7, ${alpha})`,
      `rgba(244, 67, 54, ${alpha})`,
      `rgba(156, 39, 176, ${alpha})`,
      `rgba(0, 188, 212, ${alpha})`
    ];
    return colors[index % colors.length];
  }
}