import { ADD_TODO,GET_TODOS,MARK_COMPLETE,DELETE_TODO } from "../types"

export const getTodo = () => async dispatch => {
    try {
        dispatch({
            type: GET_TODOS,
            payload: {}
        })
    } catch (error) {
        console.log(error)
    }
}

export const markComplete = id => dispatch => {
    dispatch({
        type: MARK_COMPLETE,
        payload: id
    })
}

export const addTodo = newTodo => async dispatch => {
    try {
        dispatch({
            type: ADD_TODO,
            payload: newTodo
        })
    } catch (error) {
        console.log(error)
    }


}

export const deleteTodo = id => async dispatch => {
    try {
        dispatch({
            type: DELETE_TODO,
            payload: id
        })
    } catch (error) {
        console.log(error)
    }
    
}

