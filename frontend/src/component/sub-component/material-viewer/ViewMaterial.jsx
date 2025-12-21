import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios'

import SlideExplanation from './slide-template/SlideExplanation';
import SlideExample from './slide-template/SlideExample';

function ViewMaterial ({ material }) {
    const [materialData, setMaterialData] = useState(null);
    const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
    const [err, setErr] = useState(null);

    useEffect(() => {
        const ac = new AbortController();
        let active = true;

        // Fetch material
        axios.get(`/db/material`, {
            signal: ac.signal,
            params: {
                material_id: material?.id,
                subject_id: material?.subject_id,
                topic: material?.topic,
                // redefine /db/material and remove filename
            }
        })
        .then(response => {
            /* returns an array of material slide info: 
                {
                slides: 
                    [
                    {subtitle: introduction,
                        content: (introduction point form),
                        slide_type: explanation,
                        page:1},
                    {subtitle: cosine,
                        content: (cosine point form),
                        slide_type: explanation,
                        page:2},
                    {subtitle: example,
                        content: example question,
                        slide_type: example,
                        page:3},
                    {subtitle: conclusion,
                        content: conclusion point form,
                        slide_type: explanation,
                        page:4},
                    ]
                }
            */
            if (!active) return;
            setMaterialData(response.data);
            setCurrentSlideIndex(0);
        })
        .catch(e => {
            if (active) setErr("Unable to Slide");
        });
        return () => {
            active = false;
            ac.abort();
        }
    }, [material]);

    if (err) return (
        <div>
            {err}
        </div>
    )

    if (!materialData) return <div>Loading...</div>;

    const slides = materialData.slides || [];
    const totalSlides = slides.length;
    const currentSlide = slides[currentSlideIndex];

    const handleNextSlide = () => {
        if (currentSlideIndex < totalSlides - 1) {
            setCurrentSlideIndex((prev) =>
                prev < totalSlides - 1 ? prev + 1 : prev
            );
        }
    };

    const handlePrevSlide = () => {
        if (currentSlideIndex > 0) {
            setCurrentSlideIndex((prev) =>
                prev > 0 ? prev - 1 : prev
            );
        }
    };

    const progressPercentage = totalSlides > 0 ? ((currentSlideIndex + 1) / totalSlides) * 100 : 0;

    // Slide component wip
    const renderSlide = () => {
        if (!currentSlideIndex) return null;
        if (currentSlide.slide_type === 'explanation') {
            return <SlideExplanation slide={currentSlide} />;
        }
        if (currentSlide.slide_type === 'example') {
            return <SlideExample slide={currentSlide} />;
        }
        return <div>Unknown slide type</div>;
    }

    return (
        <div className="slide-viewer">
            <div className="slide-block">
                <div className="slide-container">
                    {/* left click zone */}
                    <div className="click-zone left" onClick={handlePrevSlide} />
                    {/* slide content */}
                    <div className="slide-content">
                        {renderSlide()}
                    </div>
                    {/* right click zone */}
                    <div className="click-zone right" onClick={handleNextSlide} />                
                </div>
                <div className="slide-progress-bar">
                    <div className="slide-progress-bar-fill" style={{ width: `${progressPercentage}%` }} />
                </div>
            </div>
            <div className="slide-progress-text">
                Slide {currentSlideIndex + 1} of {totalSlides}
            </div>
        </div>
    );
}

export default ViewMaterial;