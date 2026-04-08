import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '../api/projects'
import { useProjectStore } from '../stores/useProjectStore'

export const useProjects = () => {
  const setProjects = useProjectStore((state) => state.setProjects)

  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const data = await projectsApi.getAll()
      setProjects(data.projects || [])
      return data.projects || []
    },
  })
}

export const useProject = (projectId) => {
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject)

  return useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const data = await projectsApi.getById(projectId)
      setCurrentProject(data.project)
      return data.project
    },
    enabled: !!projectId,
  })
}

export const useCreateProject = () => {
  const queryClient = useQueryClient()
  const addProject = useProjectStore((state) => state.addProject)

  return useMutation({
    mutationFn: ({ name, description }) => projectsApi.create(name, description),
    onSuccess: (data) => {
      addProject(data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export const useUpdateProject = () => {
  const queryClient = useQueryClient()
  const updateProject = useProjectStore((state) => state.updateProject)

  return useMutation({
    mutationFn: ({ projectId, updates }) => projectsApi.update(projectId, updates),
    onSuccess: (data, variables) => {
      updateProject(variables.projectId, data.project)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project', variables.projectId] })
    },
  })
}

export const useDeleteProject = () => {
  const queryClient = useQueryClient()
  const removeProject = useProjectStore((state) => state.removeProject)

  return useMutation({
    mutationFn: (projectId) => projectsApi.delete(projectId),
    onSuccess: (_, projectId) => {
      removeProject(projectId)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}
