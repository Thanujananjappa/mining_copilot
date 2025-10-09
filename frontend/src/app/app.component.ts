import { Component, OnInit } from '@angular/core';
import { ApiService } from './services/api.service';

interface SystemStatus {
  database: boolean;
  chromadb: boolean;
  mistral_ai: boolean;
  services_ready: boolean;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'Mining Intelligence System';
  isHealthy = false;
  selectedLanguage = 'en';
  languages: any = {};
  systemStatus: SystemStatus | null = null;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.checkHealth();
    this.loadLanguages();
    this.loadSystemStatus();
  }

  checkHealth(): void {
    this.apiService.healthCheck().subscribe({
      next: (response) => {
        this.isHealthy = response.status === 'healthy';
      },
      error: (error) => {
        this.isHealthy = false;
      }
    });
  }

  loadSystemStatus(): void {
    this.apiService.getSystemStatus().subscribe({
      next: (response) => {
        if (response.success) {
          this.systemStatus = response.status;
        }
      },
      error: (error) => {
        console.error('Error loading system status:', error);
      }
    });
  }

  loadLanguages(): void {
    this.apiService.getLanguages().subscribe({
      next: (response) => {
        if (response.success) {
          this.languages = response.languages;
        } else {
          // Fallback languages
          this.languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'hi': 'Hindi'
          };
        }
      },
      error: (error) => {
        // Fallback if API fails
        this.languages = {
          'en': 'English',
          'es': 'Spanish',
          'fr': 'French',
          'hi': 'Hindi'
        };
      }
    });
  }

  onLanguageChange(event: any): void {
    this.selectedLanguage = event.target.value;
  }

  suggestQuestion(question: string): void {
    // This will be handled by the chat component
    const chatComponent = document.querySelector('app-chat');
    if (chatComponent) {
      // We'll use a custom event to pass the suggestion to chat component
      const event = new CustomEvent('suggestQuestion', { detail: question });
      chatComponent.dispatchEvent(event);
    }
  }
}