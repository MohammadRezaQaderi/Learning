import Header from "./components/Header";
import Tasks from "./components/Tasks";
import AddTask from "./components/AddTask";
import Footer from "./components/Footer";
import { useState, useEffect } from "react"

// import React from "react";
function App() {
  const [showAddTask, setShowAddTask] = useState(false)
  const [tasks, setTasks] = useState([])
  
  useEffect(()=>{
    const getTasks = async () => {
      const tasksFromServer = await fetchTasks()
      setTasks(tasksFromServer)
    }
    getTasks()
  }, [])
  
  // Fetch tasks
  const fetchTasks = async () => {
    const res = await fetch ('http://localhost:5000/tasks')
    const data = await res.json()
    return data
  }

  // Fetch task
  const fetchTask = async (id) => {
    const res = await fetch (`http://localhost:5000/tasks/${id}`)
    const data = await res.json()
    return data
  }

  
  // delete the UI form for the Tasks
  const deleteTask = async (id) => {
    await fetch(`http://localhost:5000/tasks/${id}`, {method: 'DELETE'})
    setTasks(tasks.filter((task) => task.id !== id))
  }

  // Add tasks
  const addTask = async (task) =>{
    const res = await fetch(`http://localhost:5000/tasks/`, 
    {
      method: 'POST',
      headers:{
        'Content-type': 'application/json'
      },
      body:JSON.stringify(task)
    })
    const data = await res.json()
    setTasks([...tasks,data])
    // const id = Math.floor(Math.random()*555)+27
    // //make new task
    // const newTask = {id, ...task}
    // // added to previous tasks
    // setTasks([...tasks, newTask]) 
  }

  // Toggle the Reminder
  const toggleReminder = async (id) => {
    const taskToToggle = await fetchTask(id)
    const updTask = {...taskToToggle, reminder:!taskToToggle.reminder}
    const res = await fetch(`http://localhost:5000/tasks/${id}`,{
      method: 'PUT',
      headers:{
        'Content-type': 'application/json'
      },
      body: JSON.stringify(updTask)
    })
    const data = await res.json()
    setTasks(
      tasks.map((task) =>
         task.id === id ? {...task, reminder: data.reminder} : task))
  }


  return (
      <div className="App">
        <Header onAdd={() => setShowAddTask(!showAddTask) } showAdd = {showAddTask} />
        {showAddTask && <AddTask onAdd={addTask} />}
        {tasks.length > 0 ? <Tasks tasks={tasks} onDelete = {deleteTask} onToggle = {toggleReminder}/> : "There is no Task"}
        <Footer />
      </div>
    );
}
  
// class App extends React.Component{
//   render(){
//     return <h1>This is class model</h1>
//   }
// }
export default App;
