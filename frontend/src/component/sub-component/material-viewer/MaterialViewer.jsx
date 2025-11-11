import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import MaterialViewer_materialList from './MaterialViewer_materialList';
import MaterialViewer_subjectList from './MaterialViewer_subjectList';

function MaterialViewer(props) {
    useEffect(() => {
        if (props.activeSection !== 'materials') return;
    }, [props.activeSection]);
    return (
        <MaterialViewer_subjectList {...props} />
    )
}

export default MaterialViewer;