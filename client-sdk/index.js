"use strict";
class InfraClient {
  constructor(o={}) { this.host=o.host||"http://localhost:8000"; this.timeout=o.timeout||60000; }
  async _req(m,p,b) {
    const c=new AbortController(),t=setTimeout(()=>c.abort(),this.timeout);
    try {
      const r=await fetch(`${this.host}${p}`,{method:m,headers:{"Content-Type":"application/json"},body:b?JSON.stringify(b):undefined,signal:c.signal});
      if(!r.ok) throw new Error(`InfraOS API ${r.status}`);
      return r.json();
    } finally { clearTimeout(t); }
  }
  cluster() { return this._req("GET","/api/v1/k8s/cluster",null); }
  pods(namespace="") { return this._req("GET",`/api/v1/k8s/pods${namespace?"?namespace="+namespace:""}`,null); }
  deployments(namespace="") { return this._req("GET",`/api/v1/k8s/deployments${namespace?"?namespace="+namespace:""}`,null); }
  nlQuery(question) { return this._req("POST","/api/v1/k8s/nl-query",{query:question}); }
  analyzeIncident(description,symptoms=[]) { return this._req("POST","/api/v1/incident/analyze",{description,symptoms}); }
  remediate(action,namespace,resourceName) { return this._req("POST","/api/v1/remediate",{action,namespace,resource_name:resourceName}); }
  alerts() { return this._req("GET","/api/v1/alerts",null); }
  metrics() { return this._req("GET","/api/v1/metrics/snapshot",null); }
  health() { return this._req("GET","/health",null); }
}
module.exports=InfraClient;
