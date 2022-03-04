def sort_dependencies(packages, package_name):
    package_dependencies = []
    if len(packages[package_name]) == 0:
        return package_dependencies
    else :
        for x in packages[package_name]:
            for i in range(len(packages[x])):
                if packages[x][i] not in package_dependencies:
                    package_dependencies.append(packages[x][i])
    
    package_dependencies.sort()

    return package_dependencies
