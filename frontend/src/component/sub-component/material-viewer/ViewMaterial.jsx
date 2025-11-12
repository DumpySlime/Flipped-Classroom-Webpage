import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';

function ViewMaterial ({ material }, { activeSection }) {
    const [index, setIndex] = useState(0);

    useEffect(() => {
        if (activeSection !== 'material-viewer') return;
    }, [activeSection]);

    return (
        <div className="slide-viewer">
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                {index > 0 &&
                <button onClick={() => setIndex(index - 1)}>&lt;</button>
                }
                <div className="slide-content">
                {/* For images */}
                {/* <img src={slides[index]} alt={`slide ${index + 1}`} /> */}
                {/* For HTML */}
                <div dangerouslySetInnerHTML={{ __html: slides[index] }} />
                </div>
                {index < slides.length - 1 &&
                <button onClick={() => setIndex(index + 1)}>&gt;</button>
                }
            </div>
        </div>
    );
}

export default ViewMaterial;