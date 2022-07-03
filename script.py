import os
from os import path
from xml.dom import minidom
from pyvis.network import Network

# Путь к папке с сервисами
projectsFolderPath = "D:\\Work\\QuGo\\prj\\themonolith"

# Только локальные связи проектов, без внешних зависимостей
onlyLocalReferences = True

# Группировать связи по solution
groupReferences = False

class Project:
    def __init__(self):
        self.name = ""
        self.packageReferences = []
        self.projectReferences = []

    def parse(self, csprojPath):
        # Получение имени сервиса
        self.name = path.splitext(path.basename(csprojPath))[0]

        # установленные пакеты
        packageReferences = minidom.parse(csprojPath).getElementsByTagName('PackageReference')
        for item in packageReferences:
            try:
                appendVal = item.attributes['Include'].value
                if (appendVal.lower().find("test") == -1):
                    self.packageReferences.append(appendVal)
            except: pass
        # ссылки на другие проекты
        projectReferences = minidom.parse(csprojPath).getElementsByTagName('ProjectReference')
        for item in projectReferences:
            try:
                appendVal = path.splitext(path.basename(item.attributes['Include'].value))[0]
                if (appendVal.lower().find("test") == -1):                    
                    self.projectReferences.append(appendVal)
            except: pass
        return self


class Solution:
    def __init__(self, name):
        self.name = name
        self.projects = []


# список решений
solutionList = []

# получение списка решений и их состава
for root, dirs, files in os.walk(projectsFolderPath):
    for file in files:
        if(file.endswith(".sln")):
            solution = Solution(path.splitext(file)[0])
            with open(path.join(root, file), "r") as readFile:
                for line in readFile.readlines():
                    if line.find("Project(") != -1:
                        csprojPath = line.split(",")[1].replace('"','')
                        if csprojPath.lower().find("test") == -1:
                            if csprojPath.endswith(".csproj"):
                                project = Project().parse(root + "\\" + csprojPath.strip())
                                solution.projects.append(project)
            solutionList.append(solution)

# Отображать только локальные сервисы
if onlyLocalReferences:
  localProjectNames = [project.name for solution in solutionList for project in solution.projects]
  for solution in solutionList:
    for project in solution.projects:
        project.packageReferences = set(project.packageReferences).intersection(set(localProjectNames))
        project.projectReferences = set(project.projectReferences).intersection(set(localProjectNames))

# Не отображать указанные сервисы
excludeProjectNames = [
    # 'SP.Service.Common.Filters', 
    # 'SP.Service.Common.Results', 
    # 'SP.Service.Common.Application',
    # 'SP.Service.Common.Utils',
    # 'SP.Service.Common.Rules',
    # 'SP.Market.Identity.Common',    
    # 'SP.Market.Barcode.Service',
    # 'SP.Market.Barcode.Common',
    # 'SP.Market.SMS.Service',
    # 'Stecpoint.SmsRu',
    # 'SP.Market.SMS.Common',
    # 'SP.Service.Configuration.Jaeger',
    # 'SP.Service.Configuration.Swagger',
    # 'Stecpoint.GP.CategorizationTaskQueue.Api',
    # 'Stecpoint.GP.CategorizationTaskQueue.Model',
	  # 'Stecpoint.GP.CategorizationTaskQueue.Dal',
	  # 'Stecpoint.GP.CategorizationTaskQueue.Application',
	  # 'Stecpoint.GP.CategorizationTaskQueue.Events.Common',
]
for solution in solutionList:
    for project in solution.projects:
        project.packageReferences = set(project.packageReferences).difference(set(excludeProjectNames))
        project.projectReferences = set(project.projectReferences).difference(set(excludeProjectNames))

got_net = Network(height='1000px',
                  width='100%',
                  bgcolor='#222222',
                  font_color='white',
                  notebook=True)

got_net.barnes_hut()

if groupReferences == False:
    groupNumber = 0
    for solution in solutionList:
        groupNumber +=1
        for project in solution.projects:
            got_net.add_node(project.name, project.name, title=project.name, group=groupNumber)
            for reference in project.packageReferences:
                got_net.add_node(reference, reference, title=reference, group=groupNumber)
                got_net.add_edge(project.name, reference)
            for reference in project.projectReferences:
                got_net.add_node(reference, reference, title=reference, group=groupNumber)
                got_net.add_edge(project.name, reference)
else:
    for solution in solutionList:
        got_net.add_node(solution.name, solution.name, title=solution.name)
        curReferenses = set([package for project in solution.projects for package in project.packageReferences])
        if curReferenses.__len__() != 0:
            for solutionSearch in solutionList:
                if solution.name != solutionSearch.name:
                    for project in solutionSearch.projects:
                        if any(project.name in reference for reference in curReferenses):
                            got_net.add_node(solutionSearch.name, solutionSearch.name, title=solutionSearch.name)
                            got_net.add_edge(solution.name, solutionSearch.name)


neighbor_map = got_net.get_adj_list()

# добавить данные о соседях в узлы
for node in got_net.nodes:
    node['title'] += ' Neighbors:<br>' + '<br>'.join(neighbor_map[node['id']])
    node['value'] = len(neighbor_map[node['id']])

got_net.set_options("""
var options = {
  "nodes": {
    "borderWidth": 2,
    "borderWidthSelected": 3,
    "color": {
      "highlight": {
        "border": "rgba(8,178,58,1)",
        "background": "rgba(43,255,144,1)"
      },
      "hover": {
        "border": "rgba(233,45,36,1)",
        "background": "rgba(255,193,104,1)"
      }
    },
    "font": {
      "color": "rgba(53,55,56,1)"
    },
    "size": 10
  },
  "edges": {
    "arrows": {
      "to": {
        "enabled": true
      }
    },
    "scaling": {
      "min": 15,
      "max": 50
    }, 
    "color": {
      "highlight": "rgba(0,247,72,1)",
      "inherit": false
    },
    "smooth": false
  },
  "physics": {
    "enabled": true,
    "barnesHut": {
     "gravitationalConstant": -30000,
     "centralGravity": 0,
      "springLength": 500,
      "springConstant": 0.001
    },
    "maxVelocity": 20,
    "minVelocity": 2
  }
}
""")

# Вывод в текст
with open("data.txt", "w") as file:
    for solution in solutionList:
        file.write(solution.name + '\n')
        for project in solution.projects:
            file.write(solution.name + ';' + project.name + '\n')
            for package in project.packageReferences:
                file.write(solution.name + ';'+ project.name +';' + package + '\n')

#got_net.show_buttons()

got_net.show('map.html')