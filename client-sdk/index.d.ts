export interface InfraClientOptions { host?: string; timeout?: number; }
export declare class InfraClient {
  constructor(options?: InfraClientOptions);
  cluster(): Promise<any>;
  pods(namespace?: string): Promise<any[]>;
  deployments(namespace?: string): Promise<any[]>;
  nlQuery(question: string): Promise<{ answer: string }>;
  analyzeIncident(description: string, symptoms?: string[]): Promise<{ root_cause: string; confidence: number; recommendations: string[] }>;
  remediate(action: string, namespace: string, resourceName: string): Promise<{ success: boolean }>;
  alerts(): Promise<any[]>;
  metrics(): Promise<any>;
  health(): Promise<{ status: string }>;
}
export default InfraClient;
