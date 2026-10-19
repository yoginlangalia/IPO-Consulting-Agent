const API_BASE = '/api';

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Companies
export const getCompanies = () => request('/companies');
export const getCompany = (id) => request(`/companies/${id}`);
export const createCompany = (data) => request('/companies', { method: 'POST', body: JSON.stringify(data) });
export const updateCompany = (id, data) => request(`/companies/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteCompany = (id) => request(`/companies/${id}`, { method: 'DELETE' });

// Documents
export const getDocuments = (companyId) => request(`/documents/company/${companyId}`);
export const getDocument = (id) => request(`/documents/${id}`);
export const deleteDocument = (id) => request(`/documents/${id}`, { method: 'DELETE' });
export const extractDocumentData = (id) => request(`/documents/extract/${id}`, { method: 'POST' });

export async function uploadDocument(companyId, file, docType) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_type', docType);

  const response = await fetch(`${API_BASE}/documents/upload/${companyId}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Questionnaire
export const getQuestionnaireSchema = () => request('/questionnaire/schema');
export const getQuestionnaireResponses = (companyId) => request(`/questionnaire/${companyId}`);
export const saveQuestionnaireResponses = (companyId, data) => request(`/questionnaire/${companyId}`, { method: 'POST', body: JSON.stringify(data) });

// Eligibility
export const getSebiRules = () => request('/eligibility/rules');
export const runEligibilityCheck = (companyId) => request(`/eligibility/check/${companyId}`, { method: 'POST' });
export const getEligibilityResults = (companyId) => request(`/eligibility/results/${companyId}`);

// Readiness
export const runReadinessScoring = (companyId) => request(`/readiness/score/${companyId}`, { method: 'POST' });
export const getReadinessResults = (companyId) => request(`/readiness/results/${companyId}`);

// Reports
export const generateReport = (companyId) => request(`/reports/generate/${companyId}`, { method: 'POST' });
export const getReports = (companyId) => request(`/reports/company/${companyId}`);
export const getReport = (id) => request(`/reports/${id}`);
export const deleteReport = (id) => request(`/reports/${id}`, { method: 'DELETE' });
