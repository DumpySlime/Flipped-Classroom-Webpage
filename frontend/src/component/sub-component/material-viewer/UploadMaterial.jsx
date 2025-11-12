import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';

function UploadMaterial ({activeSection}) {

    useEffect(() => {
        if (activeSection !== 'material-viewer') return;
    }, [activeSection]);

    return (
        <>
        </>
    );
}

export default UploadMaterial;