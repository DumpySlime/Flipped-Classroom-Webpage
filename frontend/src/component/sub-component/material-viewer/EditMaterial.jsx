import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';

function EditMaterial ({ material }, { activeSection }) {

    useEffect(() => {
        if (activeSection !== 'material-viewer') return;
    }, [activeSection]);

    return (
        <>
        </>
    );
}

export default EditMaterial;