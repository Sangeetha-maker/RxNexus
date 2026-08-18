@description('Location for Container Apps environment')
param location string = resourceGroup().location
@description('Container image for the FastAPI service')
param apiImage string
@description('Container image for the React static site')
param webImage string
@description('CORS origins, for example the deployed frontend URL')
param corsOrigins string

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'payerrx-env'
  location: location
  properties: {}
}
resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'payerrx-api'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: { ingress: { external: true, targetPort: 8000 }; registries: [] }
    template: { containers: [{ name: 'api', image: apiImage, env: [{ name: 'CORS_ORIGINS', value: corsOrigins }] }], scale: { minReplicas: 0, maxReplicas: 1 } }
  }
}
resource web 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'payerrx-web'
  location: location
  properties: { managedEnvironmentId: environment.id, configuration: { ingress: { external: true, targetPort: 80 }; registries: [] }, template: { containers: [{ name: 'web', image: webImage }], scale: { minReplicas: 0, maxReplicas: 1 } } }
}
